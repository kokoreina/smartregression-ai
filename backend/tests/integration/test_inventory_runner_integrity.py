"""Task 2.19 KH: Git -> collection -> report files -> consumer/dispatch guards.

Default tests replace only Docker transport, not collection/workflow/validation.
scripts/integrity/verify.ps1 repeats these cases with the real fixture-only worker.
SQL is a recording port; no database acceptance or production runner is implied.
"""

import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

import smartregression.adapters.runners.pytest_spike as spike
from smartregression.adapters.bounded_process import CommandFailure
from smartregression.adapters.git_local import LocalGit
from smartregression.adapters.runners.inventory_collector import FixtureInventoryCollector
from smartregression.adapters.runners.inventory_fixtures import fixture_sources
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.application.analysis import analysis_exit_code, analyze_execution
from smartregression.application.inventory_store import (
    InventoryConfiguration,
    InventoryConflict,
    InventoryMetadataError,
    prepare_inventory,
    require_complete_inventory_ids,
)
from smartregression.application.persistence import persist_report
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.cli.main import main

ROOT = Path(__file__).resolve().parents[3]
KNOWN_ID = "tests/test_inventory.py::test_one"
NATIVE_IDS = (" test[đ] ", "test[é]", "test[e\u0301]", "test_" + "x" * 9000)

# Expectations precede observations and are independent of classify/finalize helpers.
CASES = [
    ("success", "completed", None, "complete", (KNOWN_ID,), 1),
    ("empty", "completed", None, "complete", (), 1),
    ("partial", "partial", "collection_failed", "partial", (KNOWN_ID,), 1),
    ("failed", "failed", "collection_failed", None, None, 2),
    ("timeout", "failed", "discovery_timeout", None, None, 2),
    ("output_limit", "failed", "output_limit", None, None, 2),
    ("duplicate", "failed", "duplicate_test_id", None, None, 2),
    ("plugin_error", "failed", "collection_failed", None, None, 2),
    ("missing_result", "failed", "invalid_worker_result", None, None, 2),
    ("malformed_result", "failed", "invalid_worker_result", None, None, 2),
    ("unsupported_id", "failed", "invalid_collection_payload", None, None, 2),
    ("native_ids", "completed", None, "complete", NATIVE_IDS, 1),
]


class RecordingStore:
    def __init__(self):
        self.writes = []

    def save(self, write):
        self.writes.append(write)


def git(root, *args):
    return subprocess.check_output(
        [
            "git",
            "-c",
            "core.hooksPath=",
            "-c",
            "commit.gpgsign=false",
            "-C",
            str(root),
            *args,
        ],
        text=True,
        stderr=subprocess.PIPE,
        timeout=20,
    ).strip()


def transport_payload(case, *, running):
    """Declared transport observations, never execute source on the host."""
    ids = list(NATIVE_IDS) if case == "native_ids" else [KNOWN_ID]
    if case in {"empty", "failed"}:
        ids = []
    if case == "duplicate":
        ids *= 2
    if case == "unsupported_id":
        ids = ["test\0id"]
    return {
        "ids": ids,
        "exit_code": 1
        if running
        else {
            "empty": 5,
            "failed": 2,
            "partial": 2,
            "plugin_error": 3,
        }.get(case, 0),
        "collection_finished": True,
        "collection_errors": 1 if case in {"failed", "partial"} else 0,
        "reports": (
            [{"test_id": KNOWN_ID, "phase": "call", "outcome": "failed"}] if running else []
        ),
        "isolation": {
            "uid": 65534,
            "seccomp": 2,
            "no_new_privileges": True,
            "network": ["lo"],
            "memory_max": str(256 * 1024 * 1024),
            "pids_max": "64",
            "cpu_max": "100000 100000",
        },
    }


@pytest.fixture
def acquired_inventory(tmp_path, monkeypatch):
    def acquire(case):
        if "SMARTREGRESSION_INTEGRITY_IMAGE" in os.environ:
            # pytest's private 0700 directories deny Docker Desktop's host file sharing.
            shared = Path(os.environ["SMARTREGRESSION_INTEGRITY_WORKSPACE"]).absolute()
            if any(
                p.is_symlink() or p.is_junction() for p in (shared, *shared.parents)
            ) or not shared.resolve(strict=True).is_relative_to(ROOT / "var"):
                raise ValueError("unsafe_integrity_workspace")
            root = shared / uuid4().hex
        else:
            root = tmp_path / "c"
        root.mkdir()
        source = root / "input"
        source.mkdir()
        git(source, "init", "-q", "--object-format=sha1")
        git(source, "config", "user.name", "Inventory Integrity Fixture")
        git(source, "config", "user.email", "fixture@example.invalid")
        git(source, "config", "core.autocrlf", "false")
        (source / "tests").mkdir()
        (source / "tests/test_base.py").write_bytes(
            fixture_sources("success")["tests/test_inventory.py"]
        )
        git(source, "add", ".")
        git(source, "commit", "-qm", "base")
        base = git(source, "rev-parse", "HEAD")
        (source / "tests/test_base.py").unlink()
        for name, raw in fixture_sources(case).items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        git(source, "add", "-A")
        git(source, "commit", "-qm", "target")
        target = git(source, "rev-parse", "HEAD")
        # Git blobs must win over uncommitted source, including executable hooks.
        first = source / next(iter(fixture_sources(case)))
        first.write_bytes(b"raise RuntimeError('dirty_source_must_not_execute')\n")
        before = git(source, "status", "--porcelain")
        commands = []
        real_command = spike.bounded_command
        image = os.environ.get("SMARTREGRESSION_INTEGRITY_IMAGE", "sha256:" + "d" * 64)

        def command(args, timeout, cap):
            commands.append(args)
            if "SMARTREGRESSION_INTEGRITY_IMAGE" in os.environ:
                try:
                    result = real_command(args, timeout, cap)
                except CommandFailure as exc:
                    # Bounded local diagnostics for these task-owned fixtures only.
                    (root / "docker-error.log").write_bytes(exc.output)
                    raise
                if args[:3] == ["docker", "rm", "-f"]:
                    assert (
                        real_command(
                            ["docker", "ps", "-aq", "--filter", "name=^/" + args[3] + "$"],
                            15,
                            4096,
                        ).strip()
                        == b""
                    )
                return result
            if args[1] == "inspect":
                return json.dumps(
                    [
                        {
                            "Id": "f" * 64,
                            "HostConfig": {
                                "Privileged": False,
                                "NetworkMode": "none",
                                "ReadonlyRootfs": True,
                                "Memory": 256 * 1024 * 1024,
                                "PidsLimit": 64,
                                "NanoCpus": 1_000_000_000,
                            },
                            "Mounts": [{"RW": False}],
                        }
                    ]
                ).encode()
            if args[1] != "start":
                return b""
            if case == "timeout":
                raise subprocess.TimeoutExpired(args, timeout)
            if case == "output_limit":
                raise ValueError("output_limit")
            if case == "missing_result":
                return b""
            create = next(a for a in reversed(commands) if a[1] == "create")
            payload = transport_payload(case, running="run" in create)
            frame = b"SMARTREGRESSION_RESULT=" + json.dumps(payload).encode() + b"\n"
            # The allowlisted fixture prints an extra frame before the trusted worker's frame.
            return (
                b"SMARTREGRESSION_RESULT={bad json}\n" + frame
                if case == "malformed_result"
                else frame
            )

        monkeypatch.setattr(spike, "bounded_command", command)
        limits = (
            spike.Limits(timeout=2)
            if case == "timeout"
            else spike.Limits(output_bytes=8192)
            if case == "output_limit"
            else spike.Limits()
        )
        worker = spike.FixtureWorker(
            image, ROOT / "scripts/g1/worker.py", ROOT / "scripts/g1/seccomp.json", limits
        )
        collector = FixtureInventoryCollector(worker, root)
        execution = analyze_execution(
            LocalGit(source),
            authorization=RepositoryAuthorization("inventory-integrity", source),
            repository_id="inventory-integrity",
            base=base,
            target=target,
            data_kind="demo",
            inventory_collector=collector,
        )
        assert git(source, "status", "--porcelain") == before
        assert git(source, "rev-parse", "HEAD") == target
        assert not list(root.glob("inventory-*"))
        creates = [a for a in commands if a[:2] == ["docker", "create"]]
        assert len(creates) == 1
        name = creates[0][creates[0].index("--name") + 1]
        assert commands[-1] == ["docker", "rm", "-f", name]
        artifacts = root / "artifacts"
        artifacts.mkdir()
        files, store = ReportFiles(artifacts, source_repository=source), RecordingStore()
        report = execution.report
        write = persist_report(
            files,
            store,
            report=report,
            configuration=execution.configuration,
            snapshot_manifests=execution.snapshot_manifests,
            artifact_id=report.report_id,
            storage_key="run/report.json",
        )
        restored = files.read(
            write.artifact, expected_identity=report.identity, expected_report_id=report.report_id
        )
        assert restored == report
        assert len(store.writes) == 1
        assert json.loads(store.writes[0].stage_summary_json)["inventory"] == (
            report.stages.inventory.model_dump(mode="json", exclude={"data"})
        )
        (root / "observation.json").write_text(
            json.dumps(
                {
                    "case": case,
                    "transport": "docker"
                    if "SMARTREGRESSION_INTEGRITY_IMAGE" in os.environ
                    else "double",
                    "identity": report.identity.model_dump(mode="json"),
                    "inventory": restored.stages.inventory.model_dump(mode="json"),
                    "analysis_exit_code": analysis_exit_code(restored),
                    "collector": collector.last_observation,
                    "collection_cleanup_command": commands[-1],
                    "materialization_removed": not list(root.glob("inventory-*")),
                    "report_artifact": write.artifact.storage_key,
                    "sql": "recording_port_only",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        # This is only consumer metadata, not an attestation of the fixture runner profile.
        config = InventoryConfiguration(
            "integrity-fixture/1",
            "consumer-guard-fixture",
            image,
            "a" * 64,
            "b" * 64,
            "c" * 64,
        )
        inventory = prepare_inventory(
            identity=restored.identity,
            inventory_id="observed-inventory",
            stage=restored.stages.inventory,
            configuration=config,
        )
        return restored, inventory, worker, commands, artifacts / write.artifact.storage_key

    return acquire


@pytest.mark.parametrize("case,status,reason,completeness,ids,exit_code", CASES)
def test_discovery_report_round_trip_and_consumer_gate(
    acquired_inventory, capsys, case, status, reason, completeness, ids, exit_code
):
    report, inventory, _, commands, artifact = acquired_inventory(case)
    stage = report.stages.inventory
    assert stage.status == status
    assert report.analysis_status == "partial"
    assert analysis_exit_code(report) == exit_code
    assert main(["validate-report", str(artifact)]) == 0
    assert "dirty_source_must_not_execute" not in artifact.read_text("utf-8")
    capsys.readouterr()
    if ids is None:
        assert stage.data is None
        assert stage.error_code == reason
    else:
        assert tuple(stage.data.test_ids) == ids
        assert stage.data.completeness == completeness
        assert stage.data.snapshot == report.identity.target
        assert [i.code for i in stage.limitations] == ([] if reason is None else [reason])
    count = len(commands)
    if status == "completed":
        assert (
            require_complete_inventory_ids(
                inventory,
                identity=report.identity,
                configuration_sha256=inventory.configuration_sha256,
            )
            == ids
        )
    else:
        with pytest.raises(InventoryMetadataError):
            require_complete_inventory_ids(
                inventory,
                identity=report.identity,
                configuration_sha256=inventory.configuration_sha256,
            )
    assert len(commands) == count


@pytest.mark.parametrize(
    "unknown",
    [
        "tests/test_inventory.py::missing",
        "tests/test_base.py::test_one",
        "--help",
        KNOWN_ID + " ",
        " " + KNOWN_ID,
    ],
)
def test_unknown_target_id_rejected_before_any_docker_command(acquired_inventory, unknown):
    report, inventory, worker, commands, artifact = acquired_inventory("success")
    ids = require_complete_inventory_ids(
        inventory, identity=report.identity, configuration_sha256=inventory.configuration_sha256
    )
    materialized = artifact.parents[2] / "dispatch"
    materialized.mkdir()
    for name, raw in fixture_sources("success").items():
        path = materialized / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    digest = spike.snapshot_digest(materialized)
    before = len(commands)
    with pytest.raises(ValueError, match="^unknown_test$"):
        worker.run(materialized, digest, inventory=ids, test_id=unknown)
    assert len(commands) == before
    # Positive control proves the rejection did not disable dispatch altogether.
    result = worker.run(materialized, digest, inventory=ids, test_id=KNOWN_ID)
    assert result["ids"] == [KNOWN_ID]
    assert result["status"] == "test_failed"
    assert any(r["phase"] == "call" and r["outcome"] == "failed" for r in result["reports"])
    assert commands[-1][:3] == ["docker", "rm", "-f"]


def test_materialized_snapshot_change_is_rejected_before_dispatch(acquired_inventory):
    report, inventory, worker, commands, artifact = acquired_inventory("success")
    ids = require_complete_inventory_ids(
        inventory, identity=report.identity, configuration_sha256=inventory.configuration_sha256
    )
    materialized = artifact.parents[2] / "dispatch"
    materialized.mkdir()
    source = materialized / "test_inventory.py"
    source.write_bytes(fixture_sources("success")["tests/test_inventory.py"])
    digest = spike.snapshot_digest(materialized)
    source.write_bytes(b"raise RuntimeError('tampered_source_must_not_execute')\n")
    before = len(commands)
    with pytest.raises(ValueError, match="^snapshot_mismatch$"):
        worker.run(materialized, digest, inventory=ids, test_id=KNOWN_ID)
    assert len(commands) == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("repository_id", "foreign-repository"),
        ("run_id", "foreign-run"),
        ("target_commit", "0" * 40),
        ("snapshot", "0" * 64),
        ("configuration", "0" * 64),
    ],
)
def test_saved_inventory_cannot_cross_identity_or_configuration(acquired_inventory, field, value):
    report, inventory, _, commands, _ = acquired_inventory("success")
    identity, config = report.identity, inventory.configuration_sha256
    if field == "configuration":
        config = value
    elif field in {"target_commit", "snapshot"}:
        target = identity.target.model_copy(
            update={
                "commit" if field == "target_commit" else "snapshot_id": value,
            }
        )
        identity = identity.model_copy(update={"target": target})
    else:
        identity = identity.model_copy(update={field: value})
    before = len(commands)
    with pytest.raises(InventoryConflict):
        require_complete_inventory_ids(inventory, identity=identity, configuration_sha256=config)
    assert len(commands) == before


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("identity", "inventory_identity_mismatch"),
        ("relabelled_partial", "invalid_discovery_result"),
        ("infrastructure", "discovery_infrastructure_error"),
    ],
)
def test_collector_boundary_corruption_is_published_as_failure(
    acquired_inventory, monkeypatch, fault, reason
):
    original = FixtureInventoryCollector.collect

    def corrupt(self, snapshot, *, identity):
        result = original(self, snapshot, identity=identity)
        if fault == "infrastructure":
            raise OSError("private-worker-diagnostic")
        if fault == "identity":
            return replace(result, identity=replace(result.identity, target_commit="0" * 40))
        return replace(result, status="complete", reason=None)

    monkeypatch.setattr(FixtureInventoryCollector, "collect", corrupt)
    report, inventory, _, _, artifact = acquired_inventory(
        "partial" if fault == "relabelled_partial" else "success"
    )
    assert report.stages.inventory.status == "failed"
    assert report.stages.inventory.error_code == reason
    assert report.stages.inventory.data is None
    assert analysis_exit_code(report) == 2
    assert "private-worker-diagnostic" not in artifact.read_text("utf-8")
    with pytest.raises(InventoryMetadataError):
        require_complete_inventory_ids(
            inventory,
            identity=report.identity,
            configuration_sha256=inventory.configuration_sha256,
        )

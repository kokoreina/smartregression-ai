"""Actual approved Git pairs -> isolated collection -> report-bound mapping sidecars.

Only the two existing allowlisted candidate targets are supported. No checkout,
input imports, install hooks or tests run on the host. This is integration evidence,
not a selection/fault-retention benchmark.
"""

import argparse
import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from smartregression.adapters.runners.candidate_inventory import (
    CANDIDATES,
)
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.application.analysis import analysis_exit_code
from smartregression.application.mapping_artifact import MappingArtifact, verify_mapping_artifact
from smartregression.application.run_store import ReportArtifact
from smartregression.cli.main import main as cli_main
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.git.snapshots import canonical_json

ROOT = Path(__file__).resolve().parents[2]


def git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "credential.helper=",
            "-C",
            str(repo),
            *args,
        ],
        env=env,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if result.returncode:
        raise ValueError("candidate_git_acquisition_failed")
    return result.stdout.decode("utf-8").strip()


def execute(image: str) -> int:
    output = ROOT / "var" / ("mapping-workflow-" + uuid4().hex)
    if any(p.is_symlink() or p.is_junction() for p in (output, *output.parents)):
        raise ValueError("unsafe_mapping_output")
    output.mkdir(parents=True, exist_ok=False)
    ledger = dict(
        passed=False,
        data_kind="approved_candidate_integration",
        started_at=datetime.now(UTC).isoformat(),
        image_id=image,
        candidates={},
    )
    try:
        for name, (remote, target, _) in CANDIDATES.items():
            folder = output / name
            repo, workspace, artifacts = folder / "source", folder / "worker", folder / "artifacts"
            for directory in (repo, workspace, artifacts):
                directory.mkdir(parents=True)
            git(repo, "init", "-q")
            git(
                repo,
                "fetch",
                "--depth=2",
                "--no-tags",
                "--no-recurse-submodules",
                "https://github.com/" + remote + ".git",
                target,
            )
            base = git(repo, "rev-parse", target + "^1")
            output_report = artifacts / "cli-report.json"
            code = cli_main(
                [
                    "analyze",
                    "--repository",
                    str(repo),
                    "--repository-id",
                    name,
                    "--authorized-root",
                    str(repo),
                    "--base",
                    base,
                    "--target",
                    target,
                    "--inventory-candidate",
                    name,
                    "--inventory-image",
                    image,
                    "--inventory-workspace",
                    str(workspace),
                    "--mapping-artifact-root",
                    str(artifacts),
                    "--output",
                    str(output_report),
                ]
            )
            report = StageAnalysisReport.model_validate_json(output_report.read_bytes())
            assert code == analysis_exit_code(report)
            mapping_key = f"{report.identity.run_id}/{report.report_id}.mapping.json"
            mapping_raw = (artifacts / mapping_key).read_bytes()
            sidecar = MappingArtifact(
                mapping_raw,
                ReportArtifact(
                    report.report_id + "-mapping",
                    mapping_key,
                    hashlib.sha256(mapping_raw).hexdigest(),
                    len(mapping_raw),
                ),
            )
            assert report.stages.inventory.status == "completed"
            assert (
                len(report.stages.inventory.data.test_ids) == {"sqlparse": 509, "tinydb": 228}[name]
            )
            assert report.stages.graph.status in {"completed", "partial"}
            assert report.stages.impact.data is not None
            assert sidecar is not None
            document = verify_mapping_artifact(sidecar.raw, expected=sidecar, report=report)
            known = set(report.stages.inventory.data.test_ids)
            relationships = document["mapping"]["relationships"]
            assert all(item["test_id"] in known for item in relationships)
            assert document["mapping"]["safe_to_exclude"] is False
            assert document["mapping"]["status"] in {"completed", "partial"}
            files = ReportFiles(artifacts, source_repository=repo)
            raw = report.model_dump_json(indent=2).encode("utf-8") + b"\n"
            descriptor = ReportArtifact(
                report.report_id,
                f"{report.identity.run_id}/{report.report_id}.json",
                hashlib.sha256(raw).hexdigest(),
                len(raw),
            )
            files.publish(sidecar.descriptor, sidecar.raw)
            files.publish(descriptor, raw)
            assert (
                files.read(
                    descriptor,
                    expected_identity=report.identity,
                    expected_report_id=report.report_id,
                )
                == report
            )
            stored_sidecar = (artifacts / sidecar.descriptor.storage_key).read_bytes()
            verify_mapping_artifact(stored_sidecar, expected=sidecar, report=report)
            try:
                verify_mapping_artifact(
                    stored_sidecar,
                    expected=sidecar,
                    report=report.model_copy(update={"report_id": "foreign-report"}),
                )
            except ValueError:
                rejected = True
            else:
                rejected = False
            assert rejected
            ledger["candidates"][name] = dict(
                base=base,
                target=target,
                report_id=report.report_id,
                run_id=report.identity.run_id,
                native_ids=len(known),
                changed_files=len(report.stages.changes.data.files),
                mapping_status=document["mapping"]["status"],
                relationships=len(relationships),
                unresolved=len(document["mapping"]["unresolved"]),
                report_sha256=descriptor.sha256,
                mapping_sha256=sidecar.descriptor.sha256,
                wrong_report_rejected=rejected,
                cli_exit_code=code,
                collector_logs=len(list(workspace.glob("smartregression-inventory-*.log"))),
            )
            logs = list(workspace.glob("smartregression-inventory-*.log"))
            assert len(logs) == 1
            # Query the exact nonce name produced by this CLI collection; do not
            # stop or inspect unrelated containers, and never infer cleanup from logs.
            remaining = subprocess.check_output(
                ["docker", "ps", "-aq", "--filter", "name=^/" + logs[0].stem + "$"],
                timeout=15,
            )
            assert not remaining.strip()
            ledger["candidates"][name]["container_removed"] = True
        ledger["passed"] = True
    except Exception as exc:
        # Keep credentials, subprocess diagnostics and source out of the shared ledger.
        ledger.update(error_code="mapping_workflow_failed", error_type=type(exc).__name__)
    finally:
        ledger["finished_at"] = datetime.now(UTC).isoformat()
        (output / "evidence.json").write_bytes(canonical_json(ledger))
        print(json.dumps(dict(passed=ledger["passed"], evidence=str(output / "evidence.json"))))
    return 0 if ledger["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    raise SystemExit(execute(parser.parse_args().image))

"""Actual Docker discovery checks on byte-allowlisted, task-authored Git fixtures only."""

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from smartregression.adapters.git_local import LocalGit
from smartregression.adapters.runners.inventory_collector import FixtureInventoryCollector
from smartregression.adapters.runners.inventory_fixtures import FIXTURE_CASES, fixture_sources
from smartregression.adapters.runners.pytest_spike import FixtureWorker, Limits
from smartregression.application.analysis import analysis_exit_code, analyze
from smartregression.application.snapshots import RepositoryAuthorization


def execute(image: str, output: Path) -> None:
    project = Path(__file__).resolve().parents[2]
    requested_output = output.absolute()
    if any(
        p.is_symlink() or p.is_junction() for p in (requested_output, *requested_output.parents)
    ):
        raise ValueError("unsafe_output_directory")
    output = requested_output.resolve()
    if (
        output == project / "var"
        or not output.is_relative_to(project / "var")
        or any(p.is_symlink() or p.is_junction() for p in (output, *output.parents))
    ):
        raise ValueError("unsafe_output_directory")
    output.mkdir(parents=True, exist_ok=False)
    ledger = {
        "scope": "owned_fixture_inventory_only",
        "image_id": image,
        "started_at": datetime.now(UTC).isoformat(),
        "cases": {},
        "passed": False,
    }

    def git(root: Path, *args: str) -> str:
        return subprocess.check_output(
            [
                "git",
                "-c",
                "core.hooksPath=" + str(output / "empty-hooks"),
                "-c",
                "commit.gpgsign=false",
                "-C",
                str(root),
                *args,
            ],
            text=True,
            stderr=subprocess.PIPE,
            timeout=15,
        ).strip()

    try:
        (output / "empty-hooks").mkdir()
        for case in FIXTURE_CASES:
            case_root = output / case
            source_root = case_root / "source"
            source_root.mkdir(parents=True)
            git(source_root, "init", "-q")
            git(source_root, "config", "user.name", "Owned Inventory Fixture")
            git(source_root, "config", "user.email", "fixture@example.invalid")
            git(source_root, "commit", "--allow-empty", "-qm", "owned base")
            base = git(source_root, "rev-parse", "HEAD")
            for path, raw in fixture_sources(case).items():
                file = source_root / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(raw)
            git(source_root, "add", ".")
            git(source_root, "commit", "-qm", "owned target")
            target = git(source_root, "rev-parse", "HEAD")
            limits = (
                Limits(timeout=2)
                if case == "timeout"
                else (Limits(output_bytes=8192) if case == "output_limit" else Limits())
            )
            worker = FixtureWorker(
                image, project / "scripts/g1/worker.py", project / "scripts/g1/seccomp.json", limits
            )
            collector = FixtureInventoryCollector(worker, case_root)
            report = analyze(
                LocalGit(source_root),
                authorization=RepositoryAuthorization("owned-inventory", source_root),
                repository_id="owned-inventory",
                base=base,
                target=target,
                data_kind="demo",
                inventory_collector=collector,
            )
            inventory = report.stages.inventory
            expected = {
                "success": ("completed", None),
                "empty": ("completed", None),
                "partial": ("partial", None),
                "failed": ("failed", "collection_failed"),
                "duplicate": ("failed", "duplicate_test_id"),
                "timeout": ("failed", "discovery_timeout"),
                "output_limit": ("failed", "output_limit"),
            }[case]
            observation = {
                "expected": list(expected),
                "actual": [inventory.status, inventory.error_code],
                "identity": report.identity.model_dump(),
                "configuration_sha256": collector.configuration_digest,
                "worker_observation": collector.last_observation,
                "inventory": inventory.model_dump(),
                "analysis_exit_code": analysis_exit_code(report),
            }
            ledger["cases"][case] = observation
            (case_root / "report.json").write_text(
                report.model_dump_json(indent=2), encoding="utf-8"
            )
            assert (inventory.status, inventory.error_code) == expected, case
            if case in {"success", "partial"}:
                assert inventory.data.test_ids == ["tests/test_inventory.py::test_one"]
            if case == "empty":
                assert inventory.data.test_ids == [] and inventory.data.completeness == "complete"
            if inventory.status == "failed":
                assert inventory.data is None and analysis_exit_code(report) == 2
        ledger["passed"] = True
    finally:
        ledger["finished_at"] = datetime.now(UTC).isoformat()
        (output / "evidence.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        print(json.dumps({"passed": ledger["passed"], "evidence": str(output / "evidence.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    execute(args.image, args.output)

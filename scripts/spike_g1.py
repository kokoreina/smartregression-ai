"""Reproducible owned-fixture demonstration. Does not execute input code on the host."""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from smartregression.adapters.git.local import LocalGitRepository
from smartregression.adapters.runners.docker_fixture import (
    DockerFixtureWorker,
    WorkerError,
    _events,
)
from smartregression.core.execution.config import ExecutionConfig
from smartregression.core.impact.python_structure import analyze_python

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--image", required=True, help="Approved immutable local Docker image ID sha256:..."
    )
    args = parser.parse_args()
    worker = DockerFixtureWorker(args.image)
    run_root = ROOT / "var/g1" / uuid4().hex
    run_root.mkdir(parents=True)
    repo = run_root / "repository"
    repo.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

    def git(*values: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), *values],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        ).stdout.strip()

    artifact = {
        "data_kind": "owned_fixture_spike",
        "started_at": datetime.now(UTC).isoformat(),
        "image": args.image,
        "g1_runtime": "not_run",
        "not_a_benchmark": True,
    }
    try:
        git("init", "-q")
        git("config", "user.name", "G1 owned fixture")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "core.autocrlf", "false")
        fixture = ROOT / "backend/tests/fixtures/g1"
        for source in fixture.rglob("*"):
            if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc":
                target = repo / source.relative_to(fixture)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
        (repo / "module.py").write_text("def value():\n    return 1\n", newline="\n")
        git("add", ".")
        git("-c", "commit.gpgsign=false", "commit", "-qm", "fixture base")
        base = git("rev-parse", "HEAD")
        (repo / "module.py").write_text("def value():\n    return 2\n", newline="\n")
        git("add", ".")
        git("-c", "commit.gpgsign=false", "commit", "-qm", "fixture target")
        target = git("rev-parse", "HEAD")
        adapter = LocalGitRepository(repo)
        changes = adapter.diff(base, target, rename_threshold=50)
        snapshot = run_root / "snapshot"
        snapshot.mkdir()
        for name in ["LICENSE", "module.py", "tests/test_demo.py"]:
            path = snapshot / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(adapter.read_text(target, name), encoding="utf-8", newline="\n")
        config = ExecutionConfig()
        artifact.update(
            base_sha=base,
            target_sha=target,
            changes=[c.model_dump() for c in changes],
            structure=asdict(analyze_python(adapter.read_text(target, "module.py"), "module.py")),
            config=asdict(config),
            config_hash=config.fingerprint,
        )
        inventory = worker.discover(snapshot, target, config)
        artifact["inventory"] = asdict(inventory)
        artifact["inventory_hash"] = inventory.fingerprint
        if inventory.status != "complete":
            artifact["g1_runtime"] = inventory.status
            return 2
        selected = inventory.ids[0]
        selection = {
            "target_sha": target,
            "test_id": selected,
            "inventory_hash": inventory.fingerprint,
            "snapshot_hash": inventory.snapshot_hash,
            "frozen_at": datetime.now(UTC).isoformat(),
        }
        (run_root / "selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")
        observed = worker.run_one(snapshot, target, inventory, selected, config)
        events = _events(observed.output)
        calls = [
            row for row in events if row.get("kind") == "result" and row.get("phase") == "call"
        ]
        artifact.update(
            selected_test=selected, test_exit_code=observed.returncode, execution_events=events
        )
        passed = (
            observed.returncode == 0
            and len(calls) == 1
            and calls[0].get("test_id") == selected
            and calls[0].get("outcome") == "passed"
        )
        artifact["g1_runtime"] = "demonstrated_on_owned_fixture" if passed else "failed"
        return 0 if passed else 2
    except (WorkerError, OSError, subprocess.SubprocessError, ValueError) as exc:
        artifact["g1_runtime"] = "blocked"
        artifact["failure_category"] = (
            str(exc) if isinstance(exc, WorkerError) else type(exc).__name__
        )
        return 2
    finally:
        artifact["finished_at"] = datetime.now(UTC).isoformat()
        path = run_root / "evidence.json"
        path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
        print(json.dumps({"evidence": str(path), "g1_runtime": artifact["g1_runtime"]}))


if __name__ == "__main__":
    sys.exit(main())

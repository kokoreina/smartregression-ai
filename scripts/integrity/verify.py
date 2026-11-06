"""Repeat task-owned cross-module regressions using the real isolated fixture worker."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def execute(*, runtime_only=False):
    project = Path(__file__).resolve().parents[2]
    # Git for Windows also expands .git template paths beneath each test directory.
    output = project / "var" / ("i-" + uuid4().hex)
    if any(p.is_symlink() or p.is_junction() for p in (output, *output.parents)):
        raise ValueError("unsafe_output_directory")
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.pop("SMARTREGRESSION_INTEGRITY_IMAGE", None)
    env["PYTHONPATH"] = str(project / "backend/src")
    ledger = {
        "scope": "task-2.19-owned-fixture-integrity",
        "started_at": datetime.now(UTC).isoformat(),
        "sql": "recording_port_only_no_database_run",
        "runtime_only": runtime_only,
        "checks": [],
        "passed": False,
    }

    def run(name, args, *, timeout=600):
        print("Running " + name, flush=True)
        log = output / (name + ".log")
        with log.open("wb") as stream:
            result = subprocess.run(
                args,
                cwd=project,
                env=env,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        ledger["checks"].append(
            {"name": name, "args": args, "exit_code": result.returncode, "log": log.name}
        )
        print(log.read_text("utf-8", errors="replace"), flush=True)
        if result.returncode:
            raise RuntimeError(name + " failed; inspect local log")

    try:
        ledger["base_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=project,
            text=True,
            timeout=15,
        ).strip()
        ledger["source_sha256"] = {
            path: hashlib.sha256((project / path).read_bytes()).hexdigest()
            for path in (
                "backend/tests/integration/test_inventory_runner_integrity.py",
                "backend/src/smartregression/adapters/runners/pytest_spike.py",
                "backend/src/smartregression/adapters/runners/inventory_collector.py",
                "scripts/g1/worker.py",
                "scripts/g1/seccomp.json",
            )
        }
        if not runtime_only:
            run("pytest-default", [sys.executable, "-m", "pytest"])
            run("ruff-check", [sys.executable, "-m", "ruff", "check", "."])
            run("ruff-format", [sys.executable, "-m", "ruff", "format", "--check", "."])
            run("contract-check", [sys.executable, "scripts/export_contracts.py", "--check"])
        run(
            "fixture-image",
            [
                "docker",
                "build",
                "-t",
                "smartregression-integrity:owned",
                "-f",
                "scripts/g1/Dockerfile",
                "scripts/g1",
            ],
        )
        image = subprocess.check_output(
            [
                "docker",
                "image",
                "inspect",
                "smartregression-integrity:owned",
                "--format",
                "{{.Id}}",
            ],
            cwd=project,
            text=True,
            timeout=15,
        ).strip()
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
            raise ValueError("pinned_image_required")
        ledger["image_id"] = image
        env["SMARTREGRESSION_INTEGRITY_IMAGE"] = image
        workspace = output / "w"
        workspace.mkdir()
        env["SMARTREGRESSION_INTEGRITY_WORKSPACE"] = str(workspace)
        junit = output / "runtime.xml"
        run(
            "docker-integrity",
            [
                sys.executable,
                "-m",
                "pytest",
                "backend/tests/integration/test_inventory_runner_integrity.py",
                "-q",
                "--basetemp",
                str(output / "t"),
                "--junitxml",
                str(junit),
            ],
        )
        cases = ET.parse(junit).findall(".//testcase")
        if len(cases) != 26 or any(
            c.find(tag) is not None for c in cases for tag in ("failure", "error", "skipped")
        ):
            raise RuntimeError("runtime case count or acceptance mismatch")
        ledger["runtime_cases"] = [c.attrib["name"] for c in cases]
        ledger["observations"] = [
            str(p.relative_to(output)) for p in sorted(output.rglob("observation.json"))
        ]
        ledger["passed"] = True
    finally:
        ledger["finished_at"] = datetime.now(UTC).isoformat()
        evidence = output / "evidence.json"
        evidence.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        print(json.dumps({"passed": ledger["passed"], "evidence": str(evidence)}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-only", action="store_true")
    execute(runtime_only=parser.parse_args().runtime_only)

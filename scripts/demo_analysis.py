"""Reproduce 2.13 on an owned Git fixture; never execute the fixture's Python."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from smartregression.application.evidence_store import (
    EVIDENCE_FORMAT,
    decode_evidence,
    prepare_evidence,
)
from smartregression.application.persistence import bundle_from_report
from smartregression.contracts.stages import StageAnalysisReport


def reproduce(output: Path) -> dict:
    """Create a NEW fixture/evidence directory. No existing repository is edited."""
    output = output.absolute()
    output.mkdir()  # Exclusive; the caller creates/owns the parent.
    repository = output / "input"
    repository.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_TERMINAL_PROMPT="0",
        GIT_AUTHOR_DATE="2026-11-03T00:00:00+00:00",
        GIT_COMMITTER_DATE="2026-11-03T00:00:00+00:00",
    )

    def git(*args: str) -> str:
        return subprocess.check_output(
            [
                "git",
                "-c",
                "core.hooksPath=",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "user.name=SmartRegression Demo",
                "-c",
                "user.email=demo@example.invalid",
                "-c",
                "core.autocrlf=false",
                "-C",
                str(repository),
                *args,
            ],
            env=env,
            text=True,
            stderr=subprocess.PIPE,
            timeout=30,
        ).strip()

    git("init", "-q", "--initial-branch=fixture")
    (repository / "a.py").write_bytes(b"def f():\n    return 1\n")
    (repository / "old.py").write_bytes(b"def renamed():\n    return 10\n")
    (repository / "deleted.py").write_bytes(b"def gone():\n    return 1\n")
    git("add", ".")
    git("commit", "-qm", "owned-demo-base")
    base = git("rev-parse", "HEAD")
    (repository / "a.py").write_bytes(b"def f():\n    return 2\n")
    (repository / "b.py").write_bytes(b"import a\n")
    (repository / "old.py").rename(repository / "new.py")
    (repository / "deleted.py").unlink()
    git("add", "-A")
    git("commit", "-qm", "owned-demo-target")
    target = git("rev-parse", "HEAD")
    (repository / "a.py").write_bytes(b"def broken(\n")
    git("add", ".")
    git("commit", "-qm", "owned-demo-parse-failure")
    broken = git("rev-parse", "HEAD")
    # The committed input stays frozen even when the working tree is unusable.
    (repository / "a.py").write_bytes(b"DIRTY WORKING TREE - DO NOT PARSE\n")

    evidence = {
        "data_kind": "demo",
        "python": sys.version.split()[0],
        "git": git("--version"),
        "cwd": str(Path.cwd()),
        "repository_id": "workflow-demo",
        "base": base,
        "target": target,
        "broken_target": broken,
        "runs": [],
        "limits": {
            "max_files": 1000,
            "max_file_bytes": 1_000_000,
            "max_total_bytes": 16_000_000,
            "python_source_bytes": 256_000,
        },
        "comparison_mode": "direct_two_tree",
        "graph_revision": "target",
        "persistence": "json_artifacts_only",
    }
    for name, revision, expected in (
        ("thin", target, 1),
        ("failure", broken, 2),
        ("empty", base, 1),
    ):
        report_path = output / f"{name}.json"
        command = [
            sys.executable,
            "-m",
            "smartregression.cli.main",
            "analyze",
            "--repository",
            str(repository),
            "--repository-id",
            "workflow-demo",
            "--authorized-root",
            str(repository),
            "--base",
            base,
            "--target",
            revision,
            "--data-kind",
            "demo",
            "--output",
            str(report_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
        (output / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
        if result.returncode != expected or result.stdout:
            raise ValueError("demo_unexpected_cli_result")
        report = StageAnalysisReport.model_validate_json(report_path.read_text("utf-8"))
        expected_stages = (
            ("completed", "partial", "failed")
            if name == "failure"
            else ("completed", "completed", "completed")
        )
        if (
            report.data_kind != "demo"
            or report.analysis_status != "partial"
            or report.identity.repository_id != "workflow-demo"
            or report.identity.base.commit != base
            or report.identity.target.commit != revision
            or (
                report.stages.snapshots.status,
                report.stages.changes.status,
                report.stages.graph.status,
            )
            != expected_stages
            or (name == "empty" and report.stages.changes.data.components)
        ):
            raise ValueError("demo_unexpected_analysis")
        bundle = bundle_from_report(report)
        bundle_record = None
        if name != "failure":
            if bundle is None or report.stages.review_ordering.data is None:
                raise ValueError("demo_missing_integrated_producer")
            raw_bundle = prepare_evidence(bundle)
            digest = hashlib.sha256(raw_bundle).hexdigest()
            if decode_evidence(raw_bundle, EVIDENCE_FORMAT, digest, report.identity) != bundle:
                raise ValueError("demo_bundle_reload_failed")
            bundle_path = output / f"{name}.evidence.json"
            bundle_path.write_bytes(raw_bundle)
            bundle_record = {
                "path": bundle_path.name,
                "sha256": digest,
                "size_bytes": len(raw_bundle),
                "scope": "local_codec_not_database",
            }
        elif bundle is not None:
            raise ValueError("demo_failure_fabricated_bundle")
        evidence["runs"].append(
            {
                "name": name,
                "command": command,
                "exit_code": result.returncode,
                "report": report_path.name,
                "identity": report.identity.model_dump(mode="json"),
                "evidence_bundle": bundle_record,
                "stages": {
                    key: getattr(report.stages, key).status
                    for key in type(report.stages).model_fields
                },
            }
        )
    (output / "reproduction.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="NEW directory; existing parent required"
    )
    args = parser.parse_args()
    try:
        reproduce(args.output)
    except OSError, ValueError, subprocess.SubprocessError:
        print(
            "DEMO reproduction failed; inspect retained artifacts. "
            "No existing output is overwritten.",
            file=sys.stderr,
        )
        return 2
    print("DEMO reproduction verified: thin=1, failure=2, empty=1. Analysis is incomplete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

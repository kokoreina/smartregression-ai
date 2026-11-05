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

from smartregression.adapters.git_local import LocalGit
from smartregression.adapters.runners.candidate_inventory import (
    CANDIDATES,
    CandidateInventoryCollector,
)
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.application.analysis import analyze_execution
from smartregression.application.mapping_artifact import verify_mapping_artifact
from smartregression.application.run_store import ReportArtifact
from smartregression.application.snapshots import RepositoryAuthorization
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
            collector = CandidateInventoryCollector(name, image, ROOT, workspace)
            execution = analyze_execution(
                LocalGit(repo),
                authorization=RepositoryAuthorization(name, repo),
                repository_id=name,
                base=base,
                target=target,
                data_kind="real",
                mapping_collector=collector,
            )
            report, sidecar = execution.report, execution.mapping_artifact
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
                container_removed=collector.last_observation.get("container_removed") is True,
            )
            assert ledger["candidates"][name]["container_removed"]
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

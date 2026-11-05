"""Task 2.19 AN: actual Git -> report boundaries -> publication/read.

Evidence observations are labelled fixtures at the report boundary: the workflow
does not yet produce/verify them. SQL is a recording port double. Input Python is
never executed. This is not live evidence verification or PostgreSQL acceptance.
"""

import json
import subprocess
from copy import deepcopy

import pytest
from pydantic import ValidationError

from smartregression.adapters.git_local import LocalGit
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.application.analysis import analysis_exit_code, analyze_execution
from smartregression.application.persistence import persist_report
from smartregression.application.reports import validate_report_json
from smartregression.application.run_store import RunMetadataError, RunStorageError
from smartregression.application.snapshots import RepositoryAuthorization, prepare_snapshots
from smartregression.cli.main import main
from smartregression.contracts.stages import RunIdentity, StageAnalysisReport
from smartregression.core.impact.potential_impact import build_potential_impact
from smartregression.core.retrieval.context import build_retrieval_payload
from smartregression.core.retrieval.index_manifest import ChunkInput, build_index_manifest
from smartregression.core.retrieval.ranked_context import validate_retrieval_stage


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture(scope="module")
def acquired_run(tmp_path_factory):
    repo = tmp_path_factory.mktemp("identity-evidence-input")
    git(repo, "init", "-q", "--object-format=sha1")
    git(repo, "config", "user.name", "Integrity Fixture")
    git(repo, "config", "user.email", "integrity@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    (repo / "calc.py").write_bytes(b"def value():\n    return 1\n")
    (repo / "consumer.py").write_text(
        "import calc\nraise RuntimeError('input-must-not-execute')\n", encoding="utf-8"
    )
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "integrity base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "calc.py").write_bytes(b"def value():\n    return 2\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "integrity target")
    target = git(repo, "rev-parse", "HEAD")
    execution = execute(repo, base, target)
    assert execution.report.stages.changes.status == "completed"
    assert execution.report.stages.graph.status == "completed"
    return repo, execution


def execute(repo, base, target):
    return analyze_execution(
        LocalGit(repo),
        authorization=RepositoryAuthorization("integrity-fixture", repo),
        repository_id="integrity-fixture",
        base=base,
        target=target,
        data_kind="demo",
    )


class RecordingStore:
    """Records the SQL-port write; implements no database or transaction semantics."""

    def __init__(self):
        self.writes = []

    def save(self, write):
        self.writes.append(write)


@pytest.fixture
def publication(acquired_run, tmp_path):
    repo, execution = acquired_run
    root = tmp_path / "artifacts"
    root.mkdir()
    return execution, ReportFiles(root, source_repository=repo), RecordingStore()


def publish(execution, files, store, report):
    return persist_report(
        files,
        store,
        report=report,
        configuration=execution.configuration,
        snapshot_manifests=execution.snapshot_manifests,
        artifact_id=report.report_id,
        storage_key="run/report.json",
    )


def evidence_observation(execution):
    """Valid fixture observation on actual acquired identity, not a workflow producer."""
    report = execution.report
    impact = build_potential_impact(
        report.identity, report.stages.changes.data, report.stages.graph.data
    )
    candidate = next(c for c in impact.candidates if c.path == "calc.py" and c.symbol == "value")
    candidate.evidence_ids.append("evidence-target")
    data = report.model_dump(mode="json")
    data["stages"]["impact"] = {"status": "completed", "data": impact.model_dump(mode="json")}
    data["stages"]["evidence"] = {
        "status": "partial",
        "data": {
            "items": [
                {
                    "id": "evidence-target",
                    "snapshot": report.identity.target.model_dump(mode="json"),
                    "path": "calc.py",
                    "location": {"line_start": 1, "line_end": 2},
                    "symbol": "value",
                    "resolution": "unverified",
                    "support": "unverified",
                }
            ],
        },
        "limitations": [{"code": "source_verification_pending", "path": "calc.py"}],
    }
    return StageAnalysisReport.model_validate(data)


def test_valid_control_real_impact_and_unverified_evidence_round_trip(publication):
    execution, files, store = publication
    report = evidence_observation(execution)
    assert [(e.source, e.target) for e in report.stages.graph.data.edges] == [
        ("consumer.py", "calc.py"),
    ]
    assert {tuple(p.nodes) for p in report.stages.impact.data.paths} == {
        ("consumer.py", "calc.py"),
    }
    write = publish(execution, files, store, report)
    restored = files.read(
        write.artifact, expected_identity=report.identity, expected_report_id=report.report_id
    )
    assert restored == report
    assert restored.stages.evidence.status == "partial"
    assert restored.stages.evidence.data.items[0].resolution == "unverified"
    assert restored.stages.evidence.data.items[0].support == "unverified"
    assert analysis_exit_code(restored) == 1
    assert len(store.writes) == 1
    summary = json.loads(store.writes[0].stage_summary_json)
    assert summary["evidence"]["status"] == "partial"
    assert summary["evidence"]["limitations"] == [
        {"code": "source_verification_pending", "path": "calc.py"},
    ]


def corrupt_evidence(report, fault):
    """Simulate mutation after model construction, across a shallow-frozen boundary."""
    report = deepcopy(report)
    evidence = report.stages.evidence
    item = evidence.data.items[0].model_copy(update={"excerpt": "private-evidence-marker"})
    if fault == "foreign_repository":
        item = item.model_copy(
            update={
                "snapshot": item.snapshot.model_copy(
                    update={"repository_id": "another-repository"}
                ),
            }
        )
    elif fault == "foreign_commit":
        item = item.model_copy(
            update={
                "snapshot": item.snapshot.model_copy(update={"commit": "0" * 40}),
            }
        )
    elif fault == "foreign_snapshot":
        item = item.model_copy(
            update={
                "snapshot": item.snapshot.model_copy(update={"snapshot_id": "0" * 64}),
            }
        )
    elif fault == "reversed_span":
        item = item.model_copy(
            update={
                "location": item.location.model_copy(update={"line_start": 3, "line_end": 1}),
            }
        )
    elif fault == "dangling_reference":
        next(c for c in report.stages.impact.data.candidates if c.evidence_ids).evidence_ids[:] = [
            "unknown-evidence",
        ]
    elif fault == "false_completed":
        report = report.model_copy(
            update={
                "stages": report.stages.model_copy(
                    update={
                        "evidence": evidence.model_copy(
                            update={"status": "completed", "limitations": []}
                        ),
                    }
                )
            }
        )
    elif fault == "unsupported_support":
        item = item.model_copy(update={"support": "supported"})
    elif fault == "missing_verification_reason":
        item = item.model_copy(update={"resolution": "resolved", "support": "supported"})
    else:
        raise AssertionError("Unknown test fault")
    report.stages.evidence.data.items[0] = item
    return report


@pytest.mark.parametrize(
    ("fault", "expected_error"),
    [
        ("foreign_repository", "foreign_evidence_snapshot"),
        ("foreign_commit", "foreign_evidence_snapshot"),
        ("foreign_snapshot", "foreign_evidence_snapshot"),
        ("reversed_span", "invalid_line_range"),
        ("dangling_reference", "unknown_evidence_reference"),
        ("false_completed", "unverified_evidence_requires_partial_stage"),
        ("unsupported_support", "support_requires_resolved_source"),
        ("missing_verification_reason", "verification_requires_reason"),
    ],
)
def test_invalid_evidence_rejected_by_cli_and_before_publication(
    publication,
    tmp_path,
    capsys,
    fault,
    expected_error,
):
    execution, files, store = publication
    report = corrupt_evidence(evidence_observation(execution), fault)
    incoming = tmp_path / "incoming.json"
    incoming.write_text(report.model_dump_json(), encoding="utf-8")
    with pytest.raises(ValidationError, match=expected_error):
        validate_report_json(incoming.read_text("utf-8"))
    assert main(["validate-report", str(incoming)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "private-evidence-marker" not in captured.err
    assert "Traceback" not in captured.err
    with pytest.raises(RunMetadataError):
        publish(execution, files, store, report)
    assert list(files.root.iterdir()) == []
    assert store.writes == []


@pytest.mark.parametrize("path,end", [("missing.py", 2), ("calc.py", 999)])
def test_schema_valid_unresolvable_observation_never_auto_promoted(publication, path, end):
    execution, files, store = publication
    report = evidence_observation(execution)
    item = report.stages.evidence.data.items[0]
    report.stages.evidence.data.items[0] = item.model_copy(
        update={
            "path": path,
            "location": item.location.model_copy(update={"line_end": end}),
        }
    )
    write = publish(execution, files, store, report)
    restored = files.read(
        write.artifact, expected_identity=report.identity, expected_report_id=report.report_id
    )
    item = restored.stages.evidence.data.items[0]
    assert item.path == path and item.location.line_end == end
    assert item.resolution == item.support == "unverified"
    assert restored.stages.evidence.status == "partial"
    assert restored.analysis_status == "partial"
    assert analysis_exit_code(restored) == 1


@pytest.mark.parametrize("stale", ["commit", "configuration"])
def test_retrieval_rejects_stale_index_before_report_boundary(acquired_run, publication, stale):
    repo, execution = acquired_run
    _, files, store = publication
    identity = execution.report.identity
    pair = prepare_snapshots(
        LocalGit(repo),
        authorization=RepositoryAuthorization("integrity-fixture", repo),
        repository_id="integrity-fixture",
        base=identity.base.commit,
        target=identity.target.commit,
    )
    report = evidence_observation(execution)
    impact = report.stages.impact.data
    options = {"index_version": "index/1", "configuration_id": "scope-current"}
    target_chunks = [ChunkInput("calc.py", 1, 2, b"def value():\n    return 2\n")]
    valid = build_index_manifest(pair.target, target_chunks, **options)
    payload = build_retrieval_payload(pair.target, valid, impact, **options)
    retrieval = validate_retrieval_stage(pair.target, payload, strict=True)
    assert retrieval.status == "completed"
    assert [item.path for item in retrieval.data.items] == ["calc.py"]
    data = report.model_dump(mode="json")
    data["stages"]["retrieval"] = retrieval.model_dump(mode="json")
    report = StageAnalysisReport.model_validate(data)
    write = publish(execution, files, store, report)

    if stale == "commit":
        index = build_index_manifest(
            pair.base, [ChunkInput("calc.py", 1, 2, b"def value():\n    return 1\n")], **options
        )
    else:
        index = build_index_manifest(
            pair.target, target_chunks, index_version="index/1", configuration_id="scope-old"
        )
    with pytest.raises(ValueError, match="^stale_index$"):
        build_retrieval_payload(pair.target, index, impact, **options)
    restored = files.read(
        write.artifact, expected_identity=report.identity, expected_report_id=report.report_id
    )
    assert restored.stages.retrieval.data.sources[0].snapshot == identity.target
    assert restored.stages.retrieval.data.sources[0].configuration_id == "scope-current"


@pytest.mark.parametrize("scope", ["repository", "run", "base", "target", "snapshot", "report"])
def test_published_report_cannot_be_loaded_under_other_identity(publication, scope):
    execution, files, store = publication
    report = evidence_observation(execution)
    write = publish(execution, files, store, report)
    path = files.root / write.artifact.storage_key
    original = path.read_bytes()
    expected = report.identity.model_dump(mode="json")
    expected_report = report.report_id
    if scope == "repository":
        expected["repository_id"] = "another-repository"
        expected["base"]["repository_id"] = expected["target"]["repository_id"] = (
            "another-repository"
        )
    elif scope == "run":
        expected["run_id"] = "another-run"
    elif scope in {"base", "target"}:
        expected[scope]["commit"] = "0" * 40
    elif scope == "snapshot":
        expected["target"]["snapshot_id"] = "0" * 64
    else:
        expected_report = "another-report"
    with pytest.raises(RunStorageError):
        files.read(
            write.artifact,
            expected_identity=RunIdentity.model_validate(expected),
            expected_report_id=expected_report,
        )
    assert path.read_bytes() == original
    assert (
        files.read(
            write.artifact, expected_identity=report.identity, expected_report_id=report.report_id
        ).stages.evidence.status
        == "partial"
    )
    assert len(store.writes) == 1


@pytest.mark.parametrize(
    ("fault", "expected_code"),
    [
        ("authorization", "unauthorized_repository"),
        ("mutable_ref", "invalid_analysis_request"),
        ("missing_commit", "invalid_commit"),
        ("blob_object", "invalid_commit"),
    ],
)
def test_invalid_acquisition_cannot_publish_an_empty_success(
    acquired_run,
    tmp_path,
    capsys,
    fault,
    expected_code,
):
    repo, execution = acquired_run
    identity = execution.report.identity
    root, base, target = repo, identity.base.commit, identity.target.commit
    if fault == "authorization":
        root = tmp_path / "wrong-root"
        root.mkdir()
    elif fault == "mutable_ref":
        base = "HEAD"
    elif fault == "missing_commit":
        target = "0" * 40
    else:
        base = git(repo, "rev-parse", f"{target}:calc.py")
    output = tmp_path / "report.json"
    before = git(repo, "status", "--porcelain")
    assert (
        main(
            [
                "analyze",
                "--repository",
                str(repo),
                "--repository-id",
                "integrity-fixture",
                "--authorized-root",
                str(root),
                "--base",
                base,
                "--target",
                target,
                "--data-kind",
                "demo",
                "--output",
                str(output),
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert expected_code in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == "" and not output.exists()
    assert git(repo, "status", "--porcelain") == before


def test_partial_failure_survives_actual_git_publication_and_read(acquired_run, tmp_path, capsys):
    original_repo, original = acquired_run
    repo = tmp_path / "broken-input"
    git(original_repo, "clone", "-q", "--no-hardlinks", str(original_repo), str(repo))
    git(repo, "config", "user.name", "Integrity Fixture")
    git(repo, "config", "user.email", "integrity@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    root = tmp_path / "artifacts"
    root.mkdir()
    files, store = ReportFiles(root, source_repository=repo), RecordingStore()
    (repo / "calc.py").write_text("def private_broken(\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "owned parse failure")
    execution = execute(repo, original.report.identity.base.commit, git(repo, "rev-parse", "HEAD"))
    report = execution.report
    write = publish(execution, files, store, report)
    restored = files.read(
        write.artifact, expected_identity=report.identity, expected_report_id=report.report_id
    )
    assert restored.stages.changes.status == "partial"
    assert restored.stages.changes.data.files[0].limitations == ["python_parse_failed"]
    assert restored.stages.graph.status == "failed"
    assert [(i.code, i.path) for i in restored.stages.graph.limitations] == [
        ("python_parse_failed", "calc.py"),
    ]
    assert restored.stages.graph.data is None
    assert restored.analysis_status == "partial" and analysis_exit_code(restored) == 2
    assert "private_broken" not in (files.root / write.artifact.storage_key).read_text("utf-8")
    summary = json.loads(store.writes[0].stage_summary_json)
    assert summary["graph"]["status"] == "failed"
    assert summary["graph"]["error_code"] == "python_parse_failed"
    assert main(["validate-report", str(files.root / write.artifact.storage_key)]) == 0
    capsys.readouterr()

"""Orchestration with real pure producers; only Git acquisition is a double."""

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from smartregression.application.analysis import AnalysisError, analysis_exit_code, analyze
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.contracts.models import ChangedComponent
from smartregression.core.git.snapshots import TreeEntry

BASE = "a" * 40
TARGET = "b" * 40


class Source:
    def __init__(self, root: Path, before=None, after=None):
        self.repository = root
        self.before = before if before is not None else {"a.py": b"def f():\n    return 1\n"}
        self.after = (
            after
            if after is not None
            else {"a.py": b"def f():\n    return 2\n", "b.py": b"import a\n"}
        )
        self.blobs = {}
        self.calls = []

    def snapshot_entries(self, sha):
        self.calls.append(sha)
        if sha not in {BASE, TARGET}:
            raise ValueError("invalid_commit")
        entries = []
        for path, content in sorted((self.before if sha == BASE else self.after).items()):
            oid = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
            self.blobs[oid] = content
            entries.append(TreeEntry(path, "100644", oid, len(content)))
        return tuple(entries)

    def read_blob(self, oid, *, max_bytes):
        return self.blobs[oid]

    def diff(self, base, target):
        assert (base, target) == (BASE, TARGET)
        return [
            ChangedComponent(
                path=p,
                change="added"
                if p not in self.before
                else "deleted"
                if p not in self.after
                else "modified",
            )
            for p in sorted(self.before.keys() | self.after.keys())
            if self.before.get(p) != self.after.get(p)
        ]


def run(source, **kwargs):
    return analyze(
        source,
        authorization=RepositoryAuthorization("fixture", source.repository),
        repository_id="fixture",
        base=BASE,
        target=TARGET,
        data_kind="demo",
        **kwargs,
    )


def test_thin_flow_uses_real_producers_and_honest_statuses(tmp_path):
    report = run(Source(tmp_path))
    assert report.identity.repository_id == "fixture"
    assert report.identity.target.commit == TARGET
    assert report.identity.target.snapshot_id is not None
    assert report.stages.changes.data.components[-1].path == "b.py"
    assert any(
        c.symbol == "f" and c.base_location and c.target_location
        for c in report.stages.changes.data.components
    )
    assert [(e.source, e.target) for e in report.stages.graph.data.edges] == [("b.py", "a.py")]
    assert report.stages.graph.data.snapshot == report.identity.target
    for name in ("impact", "evidence", "review_ordering"):
        assert getattr(report.stages, name).status == "completed"
        assert getattr(report.stages, name).data is not None
    for name in ("retrieval",):
        assert getattr(report.stages, name).status == "not_run"
        assert getattr(report.stages, name).reason == "retrieval_backend_not_configured"
        assert getattr(report.stages, name).data is None
    assert report.stages.inventory.status == "not_run"
    assert report.stages.inventory.reason == "inventory_collector_not_configured"
    assert report.stages.inventory.data is None
    assert report.stages.review_ordering.status == "completed"
    assert report.analysis_status == "partial"
    assert analysis_exit_code(report) == 1
    assert str(tmp_path) not in report.model_dump_json()


def test_empty_diff_is_completed_changes_not_unavailable(tmp_path):
    report = run(Source(tmp_path, {}, {}))
    assert report.stages.changes.status == "completed"
    assert report.stages.changes.data.components == []
    assert report.stages.graph.status == "completed"
    assert report.stages.graph.data.nodes == []
    assert report.stages.graph.data.snapshot == report.identity.target


def test_repeat_business_payload_stable_but_run_ids_fresh(tmp_path):
    a, b = run(Source(tmp_path)), run(Source(tmp_path))
    assert a.stages == b.stages
    assert a.identity.run_id != b.identity.run_id
    assert a.report_id != b.report_id


def test_execution_retains_acquired_manifests_and_actual_settings(tmp_path, monkeypatch):
    import smartregression.application.analysis as workflow
    from smartregression.core.git.snapshots import SnapshotLimits

    acquired = []
    actual = workflow.prepare_snapshots

    def capture(*args, **kwargs):
        pair = actual(*args, **kwargs)
        acquired.append(pair)
        return pair

    monkeypatch.setattr(workflow, "prepare_snapshots", capture)
    source = Source(tmp_path)
    limits = SnapshotLimits(max_files=12, max_file_bytes=5000, max_total_bytes=60000)
    execution = workflow.analyze_execution(
        source,
        authorization=RepositoryAuthorization("fixture", tmp_path),
        repository_id="fixture",
        base=BASE,
        target=TARGET,
        limits=limits,
        data_kind="demo",
    )
    assert len(acquired) == 1
    assert source.calls == [BASE, TARGET]
    assert execution.snapshot_manifests == (acquired[0].base.manifest, acquired[0].target.manifest)
    assert execution.configuration.snapshot_limits == limits
    assert execution.configuration.python_source_limit_bytes == 256000
    assert execution.configuration.graph_policy == "target_imports"
    assert dict(execution.configuration.producer_versions) == {
        "snapshots": "snapshot/1",
        "changes": "changed-components/1",
        "graph": None,
        "impact": "bounded-static-impact/1",
        "evidence": "frozen-static-evidence/1",
        "review_ordering": execution.report.stages.review_ordering.data.rule_version,
    }
    assert execution.configuration.application_version is None
    assert execution.report.identity.target.snapshot_id == acquired[0].target.manifest.snapshot_id
    assert "configuration" not in execution.report.model_dump()
    assert "snapshot_manifests" not in execution.report.model_dump()


@pytest.mark.parametrize("repository_id", ["other", "D:/secret/repo", "bad id"])
def test_invalid_identity_or_authorization_before_source_read(tmp_path, repository_id):
    source = Source(tmp_path)
    with pytest.raises(AnalysisError):
        analyze(
            source,
            authorization=RepositoryAuthorization("fixture", tmp_path),
            repository_id=repository_id,
            base=BASE,
            target=TARGET,
        )
    assert source.calls == []


def test_wrong_authorized_path_and_mutable_ref_rejected(tmp_path):
    source = Source(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(AnalysisError, match="unauthorized_repository"):
        analyze(
            source,
            authorization=RepositoryAuthorization("fixture", other),
            repository_id="fixture",
            base=BASE,
            target=TARGET,
        )
    with pytest.raises(AnalysisError):
        analyze(
            source,
            authorization=RepositoryAuthorization("fixture", tmp_path),
            repository_id="fixture",
            base="main",
            target=TARGET,
        )
    assert source.calls == []


def test_acquisition_failure_has_no_fabricated_report(tmp_path, monkeypatch):
    source = Source(tmp_path)
    monkeypatch.setattr(
        source, "read_blob", lambda *a, **k: (_ for _ in ()).throw(ValueError("private source"))
    )
    with pytest.raises(AnalysisError, match="snapshot_acquisition_failed"):
        run(source)


def test_foreign_change_result_rejected_but_graph_can_continue(tmp_path, monkeypatch):
    import smartregression.application.analysis as workflow

    actual = workflow.identify_changes
    monkeypatch.setattr(
        workflow, "identify_changes", lambda *a, **k: replace(actual(*a, **k), repository="foreign")
    )
    report = run(Source(tmp_path))
    assert report.stages.changes.status == "failed"
    assert report.stages.graph.status == "completed"
    assert report.stages.review_ordering.reason == "dependency_failed"
    assert report.analysis_status == "partial"
    assert analysis_exit_code(report) == 2


def test_forged_graph_revision_rejected(tmp_path, monkeypatch):
    import smartregression.application.analysis as workflow

    actual = workflow.build_dependency_graph

    def foreign(**kwargs):
        return actual(**{**kwargs, "revision": BASE})

    monkeypatch.setattr(workflow, "build_dependency_graph", foreign)
    report = run(Source(tmp_path))
    assert report.stages.graph.status == "failed"
    assert report.stages.graph.error_code == "graph_snapshot_mismatch"
    assert analysis_exit_code(report) == 2


def test_diff_omission_cannot_become_completed_empty_changes(tmp_path, monkeypatch):
    source = Source(tmp_path)
    monkeypatch.setattr(source, "diff", lambda *a: [])
    report = run(source)
    assert report.stages.changes.status == "failed"
    assert report.stages.changes.error_code == "snapshot_diff_mismatch"


def test_partial_parsing_retained_and_graph_failure_not_success(tmp_path):
    report = run(Source(tmp_path, {"a.py": b"x = 1\n"}, {"a.py": b"def broken(\n"}))
    assert report.stages.changes.status == "partial"
    assert report.stages.changes.data.files[0].limitations == ["python_parse_failed"]
    assert report.stages.graph.status == "failed"
    assert analysis_exit_code(report) == 2


@pytest.mark.parametrize(
    ("content", "code"),
    [
        (b"def private_broken(\n", "python_parse_failed"),
        (b"\xffprivate-source", "python_source_not_utf8"),
        (b"\0private-source", "binary_source"),
        (b"#" + b"x" * 256_000, "source_limit"),
    ],
    ids=["parse", "encoding", "binary", "limit"],
)
def test_unchanged_graph_source_failure_retains_path_outside_diff(tmp_path, content, code):
    source = Source(
        tmp_path,
        {"ok.py": b"x = 1\n", "unchanged.py": content},
        {"ok.py": b"x = 2\n", "unchanged.py": content},
    )
    report = run(source)
    assert [f.path for f in report.stages.changes.data.files] == ["ok.py"]
    assert report.stages.changes.status == "completed"
    graph = report.stages.graph
    assert graph.status == "failed"
    assert graph.error_code == code
    assert [(issue.code, issue.path) for issue in graph.limitations] == [(code, "unchanged.py")]
    assert graph.data is None  # A validated source prefix is not an accepted graph.
    assert report.analysis_status == "partial"
    assert analysis_exit_code(report) == 2
    assert "private" not in report.model_dump_json()


def test_graph_unresolved_import_and_known_alias_gap_are_explicit(tmp_path):
    source = Source(
        tmp_path,
        {},
        {
            "pkg/__init__.py": b"",
            "pkg/a.py": b"",
            "pkg/b.py": b"",
            "pkg/use.py": b"from . import a, b\nimport missing\n",
        },
    )
    report = run(source)
    graph = report.stages.graph
    assert graph.status == "partial"
    assert {x.code for x in graph.limitations} >= {
        "target_not_in_snapshot",
        "graph_relative_alias_omission",
    }
    assert graph.data.unresolved
    assert report.stages.review_ordering.status == "partial"


def test_non_utf8_graph_fails_closed_without_source_echo(tmp_path):
    report = run(Source(tmp_path, {}, {"a.py": b"\xffprivate-source"}))
    assert report.stages.changes.status == "partial"
    assert report.stages.graph.status == "failed"
    assert "private-source" not in report.model_dump_json()


def test_foreign_acquired_pair_cannot_be_relabelled(tmp_path, monkeypatch):
    import smartregression.application.analysis as workflow

    actual = workflow.prepare_snapshots

    def wrong_pair(*args, **kwargs):
        pair = actual(*args, **kwargs)
        return replace(pair, source_repository="foreign-source")

    monkeypatch.setattr(workflow, "prepare_snapshots", wrong_pair)
    with pytest.raises(AnalysisError, match="snapshot_mismatch"):
        run(Source(tmp_path))


def test_diff_read_failure_preserves_snapshot_and_independent_graph(tmp_path, monkeypatch):
    source = Source(tmp_path)

    def fail(*args):
        raise OSError("private disk error")

    monkeypatch.setattr(source, "diff", fail)
    report = run(source)
    assert report.stages.snapshots.status == "completed"
    assert report.stages.graph.status == "completed"
    assert report.stages.changes.error_code == "change_analysis_io_error"
    assert "private disk error" not in report.model_dump_json()


def test_complete_and_failed_exit_semantics_use_real_valid_contract_examples(stage_artifacts):
    import json
    from pathlib import Path

    from smartregression.application.analysis import aggregate_status
    from smartregression.contracts.stages import StageAnalysisReport

    root = Path(__file__).resolve().parents[3]
    for suffix, expected in (("empty", 0), ("failed", 2), ("not-implemented", 1)):
        report = StageAnalysisReport.model_validate_json(
            (root / f"examples/reports/stage-report.{suffix}.json").read_text("utf-8")
        )
        assert aggregate_status(report.stages) == report.analysis_status
        assert analysis_exit_code(report) == expected
    report = StageAnalysisReport.model_validate(json.loads(json.dumps(stage_artifacts)))
    assert aggregate_status(report.stages) == "partial"
    assert analysis_exit_code(report) == 1


def test_rename_source_path_can_be_reused_in_target(tmp_path, monkeypatch):
    source = Source(
        tmp_path,
        {"old.py": b"def old():\n    return 1\n"},
        {
            "new.py": b"def old():\n    return 1\n",
            "old.py": b"def fresh():\n    return 9\n",
        },
    )
    monkeypatch.setattr(
        source,
        "diff",
        lambda *a: [
            ChangedComponent(path="new.py", previous_path="old.py", change="renamed"),
            ChangedComponent(path="old.py", change="added"),
        ],
    )
    report = run(source)
    assert report.stages.changes.status == "completed"
    assert any(c.previous_path == "old.py" for c in report.stages.changes.data.components)

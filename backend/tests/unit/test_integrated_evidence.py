from test_analysis_workflow import Source, run

from smartregression.application.analysis import analyze_execution
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.core.execution.inventory import finalize_discovery


def test_available_producers_and_verified_evidence_are_wired_once(tmp_path):
    source = Source(tmp_path)
    report = run(source)
    assert len(source.calls) == 2
    assert report.stages.impact.status == "completed"
    assert report.stages.evidence.status == "completed"
    assert report.stages.review_ordering.status == "completed"
    assert report.stages.impact.data.candidates
    assert all(item.support == "supported" for item in report.stages.evidence.data.items)
    assert report.stages.retrieval.status == "not_implemented"
    assert report.stages.inventory.reason == "inventory_collector_not_configured"
    assert report.analysis_status == "partial"


def test_failed_graph_blocks_dependent_producers_without_empty_success(tmp_path):
    report = run(Source(tmp_path, {"a.py": b"x=1\n"}, {"a.py": b"def broken(\n"}))
    for name in ("impact", "evidence", "review_ordering"):
        stage = getattr(report.stages, name)
        assert stage.status == "not_run" and stage.reason == "dependency_failed"
        assert stage.data is None


def test_partial_graph_limits_propagate_through_impact_and_evidence(tmp_path):
    report = run(Source(tmp_path, {}, {"a.py": b"import external\nx = 1\n"}))
    assert report.stages.graph.status == "partial"
    assert report.stages.impact.status == "partial"
    assert report.stages.evidence.status == "partial"
    assert report.stages.evidence.limitations


def test_unexpected_impact_failure_is_not_a_completed_empty_report(tmp_path, monkeypatch):
    import smartregression.application.analysis as workflow

    def fail(*args, **kwargs):
        raise ValueError("private source must be redacted")

    monkeypatch.setattr(workflow, "build_potential_impact", fail)
    report = run(Source(tmp_path))
    assert report.stages.impact.status == "failed"
    assert report.stages.impact.error_code == "impact_analysis_failed"
    assert report.stages.evidence.status == "not_run"
    assert "private" not in report.model_dump_json()


def test_non_python_and_deleted_origins_preserve_scope_without_crashing_impact(tmp_path):
    report = run(
        Source(
            tmp_path,
            {"a.py": b"x = 1\n", "gone.py": b"x = 2\n", "README.md": b"old"},
            {"a.py": b"x = 2\n", "README.md": b"new"},
        )
    )
    assert report.stages.impact.status == "partial"
    assert report.stages.impact.data.candidates
    codes = {issue.code for issue in report.stages.impact.limitations}
    assert "impact_non_python_change" in codes
    assert "impact_deleted_origin_target_graph" in codes


def test_actual_collector_configuration_is_captured_and_changes_are_rejected(tmp_path):
    class Collector:
        configuration_digest = "c" * 64
        changed = False

        def collect(self, snapshot, *, identity):
            result = finalize_discovery(
                expected=identity,
                observed=identity,
                payload={
                    "ids": [" test[é] "],
                    "exit_code": 0,
                    "collection_finished": True,
                    "collection_errors": 0,
                },
                termination="exited",
            )
            if self.changed:
                self.configuration_digest = "d" * 64
            return result

    source, collector = Source(tmp_path), Collector()
    kwargs = dict(
        authorization=RepositoryAuthorization("fixture", tmp_path),
        repository_id="fixture",
        base="a" * 40,
        target="b" * 40,
        inventory_collector=collector,
    )
    execution = analyze_execution(source, **kwargs)
    assert execution.configuration.inventory_configuration_digest == "c" * 64
    import json

    assert (
        json.loads(execution.configuration.canonical_bytes())["inventory_configuration_digest"]
        == "c" * 64
    )
    assert execution.report.stages.inventory.data.test_ids == [" test[é] "]
    collector.changed = True
    execution = analyze_execution(source, **kwargs)
    assert execution.report.stages.inventory.error_code == "collector_configuration_changed"
    assert execution.configuration.inventory_configuration_digest is None

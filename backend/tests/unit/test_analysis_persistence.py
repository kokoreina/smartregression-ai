"""Real analysis and report files; only Git acquisition and SQL infrastructure are doubles."""

import json
from contextlib import contextmanager
from dataclasses import replace

import pytest
from test_analysis_workflow import BASE, TARGET, Source

import smartregression.composition as composition
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.application.run_store import RunConflict, RunMetadataError, RunStorageError


@pytest.fixture
def wiring(tmp_path, monkeypatch):
    source_root, artifact_root = tmp_path / "input", tmp_path / "artifacts"
    source_root.mkdir()
    artifact_root.mkdir()
    source = Source(source_root)
    events, writes = [], []
    monkeypatch.setattr(composition, "LocalGit", lambda path: source)
    settings, engine = object(), object()

    def load():
        events.append("settings")
        return settings

    @contextmanager
    def context(actual):
        assert actual is settings
        events.append("engine")
        try:
            yield engine
        finally:
            events.append("disposed")

    class Store:
        def __init__(self, actual):
            assert actual is engine

        def save(self, write):
            # Publication must precede SQL, with exactly the referenced bytes.
            raw = (artifact_root / write.artifact.storage_key).read_bytes()
            assert json.loads(raw)["identity"]["run_id"] == write.identity.run_id
            writes.append(write)

    monkeypatch.setattr("smartregression.adapters.storage.config.load_database_settings", load)
    monkeypatch.setattr("smartregression.adapters.storage.connection.database_engine", context)
    monkeypatch.setattr("smartregression.adapters.storage.run_store.PostgresRunReportStore", Store)
    kwargs = dict(
        repository=source_root,
        repository_id="fixture",
        authorized_root=source_root,
        base=BASE,
        target=TARGET,
        data_kind="demo",
        artifact_root=artifact_root,
    )
    return kwargs, source, events, writes


def test_opt_in_wires_actual_config_manifests_and_published_report(wiring):
    kwargs, source, events, writes = wiring
    report = composition.analyze_local(**kwargs)
    assert source.calls == [BASE, TARGET]
    assert events == ["settings", "engine", "disposed"]
    assert len(writes) == 1
    write = writes[0]
    assert write.identity == report.identity
    assert {s.manifest_version for s in write.snapshots} == {"snapshot/1"}
    assert {s.materializer_version for s in write.snapshots} == {"git-blobs/1"}
    assert json.loads(write.configuration_json)["python_source_limit_bytes"] == 256000
    restored = ReportFiles(kwargs["artifact_root"], source_repository=source.repository).read(
        write.artifact, expected_identity=report.identity, expected_report_id=report.report_id
    )
    assert restored == report
    assert restored.analysis_status == "partial"


def test_default_never_loads_settings_or_creates_engine(wiring):
    kwargs, _, events, writes = wiring
    assert (
        composition.analyze_local(**(kwargs | {"artifact_root": None})).analysis_status == "partial"
    )
    assert events == writes == []


def test_graph_failure_scope_survives_publication_read_and_storage_summary(wiring):
    kwargs, source, _, writes = wiring
    source.before["unchanged.py"] = b"def private_broken(\n"
    source.after["unchanged.py"] = b"def private_broken(\n"
    report = composition.analyze_local(**kwargs)
    write = writes[0]
    restored = ReportFiles(kwargs["artifact_root"], source_repository=source.repository).read(
        write.artifact, expected_identity=report.identity, expected_report_id=report.report_id
    )
    summary = json.loads(write.stage_summary_json)
    expected = [{"code": "python_parse_failed", "path": "unchanged.py"}]
    assert restored.stages.graph.status == "failed"
    assert [item.model_dump() for item in restored.stages.graph.limitations] == expected
    assert summary["graph"]["limitations"] == expected
    assert summary["graph"]["error_code"] == "python_parse_failed"
    assert restored.stages.inventory.status == "not_run"
    assert restored.stages.inventory.reason == "inventory_collector_not_configured"
    assert summary["inventory"]["status"] == "not_run"
    assert summary["inventory"]["reason"] == "inventory_collector_not_configured"
    assert "private" not in restored.model_dump_json()


@pytest.mark.parametrize("error", [RunStorageError, RunConflict])
def test_store_failure_disposes_engine_and_keeps_complete_orphan(wiring, monkeypatch, error):
    kwargs, source, events, _ = wiring

    class FailingStore:
        def __init__(self, engine):
            pass

        def save(self, write):
            raise error()

    monkeypatch.setattr(
        "smartregression.adapters.storage.run_store.PostgresRunReportStore", FailingStore
    )
    with pytest.raises(error):
        composition.analyze_local(**kwargs)
    assert source.calls == [BASE, TARGET]  # No automatic re-analysis/retry.
    assert events[-1] == "disposed"
    paths = list(kwargs["artifact_root"].glob("*/*.json"))
    assert len(paths) == 1
    assert json.loads(paths[0].read_bytes())["analysis_status"] == "partial"


def test_publication_failure_never_calls_store_and_disposes_engine(wiring, monkeypatch):
    kwargs, _, events, writes = wiring

    def fail(*args):
        raise RunStorageError()

    monkeypatch.setattr(ReportFiles, "publish", fail)
    with pytest.raises(RunStorageError):
        composition.analyze_local(**kwargs)
    assert writes == []
    assert events[-1] == "disposed"
    assert list(kwargs["artifact_root"].iterdir()) == []


@pytest.mark.parametrize("kind", ["missing", "foreign"])
def test_invalid_execution_manifests_rejected_before_publication(wiring, monkeypatch, kind):
    kwargs, _, events, writes = wiring
    actual = composition.analyze_execution

    def wrong(*args, **kw):
        result = actual(*args, **kw)
        manifests = (
            ()
            if kind == "missing"
            else (
                replace(result.snapshot_manifests[0], repository_id="foreign"),
                result.snapshot_manifests[1],
            )
        )
        return replace(result, snapshot_manifests=manifests)

    monkeypatch.setattr(composition, "analyze_execution", wrong)
    with pytest.raises(RunMetadataError):
        composition.analyze_local(**kwargs)
    assert writes == []
    assert list(kwargs["artifact_root"].iterdir()) == []
    assert events[-1] == "disposed"


def test_unsafe_artifact_root_rejected_before_acquisition(wiring):
    kwargs, source, events, writes = wiring
    with pytest.raises(RunStorageError):
        composition.analyze_local(**(kwargs | {"artifact_root": source.repository}))
    assert source.calls == []
    assert events == ["settings"]
    assert writes == []


def test_authorization_failure_does_not_open_engine_or_publish(wiring):
    from smartregression.application.analysis import AnalysisError

    kwargs, source, events, writes = wiring
    with pytest.raises(AnalysisError, match="unauthorized_repository"):
        composition.analyze_local(**(kwargs | {"authorized_root": kwargs["artifact_root"]}))
    assert source.calls == []
    assert events == ["settings"]
    assert writes == []
    assert list(kwargs["artifact_root"].iterdir()) == []

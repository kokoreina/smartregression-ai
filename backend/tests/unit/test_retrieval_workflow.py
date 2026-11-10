"""Actual pure pipeline and guarded index files; Git/collection/metadata are doubles."""

from dataclasses import replace

import pytest
from test_analysis_workflow import BASE, TARGET, Source
from test_mapping_workflow import Collector
from test_published_lexical import MemoryStore

from smartregression.adapters.storage.index_artifacts import IndexArtifactFiles
from smartregression.application.analysis import AnalysisError, analyze_execution
from smartregression.application.retrieval import PublishedLexicalIndex, lexical_configuration
from smartregression.application.snapshots import RepositoryAuthorization


def execute(tmp_path, *, config=None):
    before = {"a.py": b"def f():\n    return 1\n", "tests/test_a.py": b"import a\n"}
    source = Source(tmp_path, before, before | {"a.py": b"def f():\n    return 2\n"})
    root = tmp_path.parent / (tmp_path.name + "-index")
    root.mkdir()
    authorization = RepositoryAuthorization("fixture", tmp_path)
    store = MemoryStore()
    index = PublishedLexicalIndex(
        source,
        authorization=authorization,
        store=store,
        artifacts=IndexArtifactFiles(root, source_repository=tmp_path),
    )
    return analyze_execution(
        source,
        authorization=authorization,
        repository_id="fixture",
        base=BASE,
        target=TARGET,
        data_kind="demo",
        mapping_collector=Collector(),
        retrieval_store=index,
        retrieval_configuration=config,
    )


def test_real_workflow_retrieves_and_binds_mapping_to_final_report(tmp_path):
    execution = execute(tmp_path)
    report = execution.report
    assert report.analysis_status == "completed"
    assert all(stage.status == "completed" for _, stage in report.stages)
    assert report.stages.retrieval.status == "completed"
    assert report.stages.retrieval.data.items
    assert all(
        item.snapshot == report.identity.target for item in report.stages.retrieval.data.items
    )
    assert execution.configuration.retrieval_configuration_digest == lexical_configuration().digest
    from smartregression.application.mapping_artifact import verify_mapping_artifact

    verify_mapping_artifact(
        execution.mapping_artifact.raw, expected=execution.mapping_artifact, report=report
    )


def test_query_cap_is_partial_not_safe_empty(tmp_path):
    execution = execute(tmp_path, config=replace(lexical_configuration(), query_terms=1))
    assert execution.report.stages.retrieval.status == "partial"
    assert any(
        i.code == "retrieval_query_limit" for i in execution.report.stages.retrieval.limitations
    )


def test_configuration_without_store_fails_before_source(tmp_path, monkeypatch):
    source = Source(tmp_path)
    monkeypatch.setattr(source, "snapshot_entries", lambda *a: pytest.fail("must reject first"))
    with pytest.raises(AnalysisError, match="retrieval_store_required"):
        analyze_execution(
            source,
            authorization=RepositoryAuthorization("fixture", tmp_path),
            repository_id="fixture",
            base=BASE,
            target=TARGET,
            retrieval_configuration=lexical_configuration(),
        )


def test_cli_rejects_index_root_without_persistence_before_acquisition(
    tmp_path, monkeypatch, capsys
):
    import smartregression.composition as composition
    from smartregression.cli.main import main

    monkeypatch.setattr(composition, "LocalGit", lambda *a: pytest.fail("must reject first"))
    assert (
        main(
            [
                "analyze",
                "--repository",
                str(tmp_path),
                "--repository-id",
                "fixture",
                "--authorized-root",
                str(tmp_path),
                "--base",
                BASE,
                "--target",
                TARGET,
                "--index-artifact-root",
                str(tmp_path),
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid_retrieval_arguments" in captured.err

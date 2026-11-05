"""Actual CLI/composition -> frozen Git -> report file -> runtime-role PostgreSQL."""

import hashlib
import json
import subprocess
from dataclasses import asdict, replace
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import URL

import smartregression.composition as composition
from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.evidence_store import PostgresEvidenceStore
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.adapters.storage.schema import (
    analysis_runs,
    artifacts,
    evidence_bundles,
    repositories,
    run_reports,
    snapshots,
)
from smartregression.application.evidence_store import EvidenceStorageError, prepare_evidence
from smartregression.application.inventory_store import InventoryConfiguration
from smartregression.application.persistence import bundle_from_report
from smartregression.application.run_store import ReportArtifact, RunConflict
from smartregression.cli.main import main
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.execution.inventory import finalize_discovery


def cli_arguments(kwargs):
    return [
        "analyze",
        *[
            item
            for key in (
                "repository",
                "repository_id",
                "authorized_root",
                "base",
                "target",
                "data_kind",
                "artifact_root",
            )
            for item in ("--" + key.replace("_", "-"), str(kwargs[key]))
        ],
        "--persist",
    ]


def test_mapping_sidecar_and_compound_report_share_exact_identity(migrated, workflow_input):
    """SQL/Git/files real; collection receipt double, real collection verified separately."""
    owner, runtime, _ = migrated
    kwargs, _ = workflow_input

    class Collector:
        configuration = InventoryConfiguration(
            "candidate-inventory/2",
            "owned-storage",
            "sha256:" + "a" * 64,
            "b" * 64,
            "c" * 64,
            "d" * 64,
        )
        configuration_digest = configuration.digest
        last_observation = None

        def collect(self, snapshot, *, identity):
            payload = dict(
                ids=["b.py::test_fixture"],
                exit_code=0,
                collection_finished=True,
                collection_errors=0,
            )
            self.last_observation = dict(
                configuration_sha256=self.configuration_digest,
                configuration=json.loads(self.configuration.canonical_bytes()),
                result=dict(
                    protocol="inventory/2",
                    mode="collect",
                    identity=asdict(identity),
                    collection=payload,
                    test_sources=dict(
                        version="pytest-item-path/1",
                        items=[dict(test_id="b.py::test_fixture", path="b.py")],
                    ),
                ),
            )
            return finalize_discovery(expected=identity, observed=identity, payload=payload)

    with owner.begin() as connection:
        connection.execute(
            repositories.insert().values(repository_id=kwargs["repository_id"], source_kind="local")
        )
    report = composition.analyze_local(**kwargs, mapping_collector=Collector())
    root = kwargs["artifact_root"] / report.identity.run_id
    raw_report = (root / (report.report_id + ".json")).read_bytes()
    mapping = json.loads((root / (report.report_id + ".mapping.json")).read_bytes())
    assert mapping["identity"] == report.identity.model_dump(mode="json")
    assert mapping["report_sha256"] == hashlib.sha256(raw_report).hexdigest()
    assert {item["test_id"] for item in mapping["mapping"]["relationships"]} == {
        "b.py::test_fixture"
    }
    assert PostgresEvidenceStore(runtime).load(report.identity) == bundle_from_report(report)
    with runtime.connect() as connection:
        catalog_digest = connection.scalar(
            sa.select(artifacts.c.sha256).where(
                artifacts.c.repository_id == report.identity.repository_id,
                artifacts.c.run_id == report.identity.run_id,
                artifacts.c.artifact_id == report.report_id,
            )
        )
    assert catalog_digest == mapping["report_sha256"]


def test_actual_cli_retrieval_uses_verified_ready_postgresql_index(
    migrated, workflow_input, capsys
):
    owner, _, _ = migrated
    kwargs, _ = workflow_input
    root = kwargs["artifact_root"]
    with owner.begin() as connection:
        connection.execute(
            repositories.insert().values(repository_id=kwargs["repository_id"], source_kind="local")
        )
    args = cli_arguments(kwargs) + ["--index-root", str(root)]
    assert main(args) == 1  # Inventory remains explicitly unconfigured.
    report = StageAnalysisReport.model_validate_json(capsys.readouterr().out)
    assert report.stages.retrieval.status == "completed"
    assert report.stages.retrieval.data.items
    assert all(i.snapshot == report.identity.target for i in report.stages.retrieval.data.items)
    assert all(
        i.location.line_end >= i.location.line_start for i in report.stages.retrieval.data.items
    )
    from smartregression.adapters.storage.schema import knowledge_indexes

    with owner.connect() as connection:
        indexes = (
            connection.execute(
                sa.select(knowledge_indexes).where(
                    knowledge_indexes.c.repository_id == report.identity.repository_id
                )
            )
            .mappings()
            .all()
        )
    assert len(indexes) == 1 and indexes[0]["state"] == "ready"
    assert indexes[0]["embedding_model"] is None
    # Corrupt persisted manifest: a fresh run must fail retrieval, not report safe empty.
    (root / indexes[0]["manifest_key"]).write_bytes(b"tampered")
    assert main(args) == 2
    failed = StageAnalysisReport.model_validate_json(capsys.readouterr().out)
    assert failed.stages.retrieval.status == "failed"
    assert failed.stages.retrieval.error_code == "retrieval_storage_failed"


def test_deleted_context_keeps_separate_base_and_target_sources(migrated, workflow_input):
    owner, _, _ = migrated
    kwargs, _ = workflow_input
    repo = kwargs["repository"]
    subprocess.check_call(["git", "-C", str(repo), "rm", "-f", "a.py"])
    subprocess.check_call(["git", "-C", str(repo), "commit", "-qm", "owned deletion"])
    deleted = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    with owner.begin() as connection:
        connection.execute(
            repositories.insert().values(repository_id=kwargs["repository_id"], source_kind="local")
        )
    report = composition.analyze_local(
        **(kwargs | dict(target=deleted)), index_root=kwargs["artifact_root"]
    )
    retrieval = report.stages.retrieval
    assert retrieval.status == "partial"
    assert {s.snapshot for s in retrieval.data.sources} == {
        report.identity.base,
        report.identity.target,
    }
    assert any(
        i.path == "a.py" and i.snapshot == report.identity.base for i in retrieval.data.items
    )
    assert not any(
        i.path == "a.py" and i.snapshot == report.identity.target for i in retrieval.data.items
    )


@pytest.fixture
def workflow_input(migrated, storage_context, tmp_path, monkeypatch):
    root = tmp_path / "input"
    root.mkdir()

    def git(*args):
        return subprocess.check_output(
            ["git", "-c", "core.hooksPath=", "-c", "commit.gpgsign=false", "-C", str(root), *args],
            text=True,
            timeout=20,
        ).strip()

    git("init", "-q")
    git("config", "user.name", "Owned Persistence Fixture")
    git("config", "user.email", "fixture@example.invalid")
    (root / "a.py").write_bytes(b"def f():\n    return 1\n")
    git("add", ".")
    git("commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    (root / "a.py").write_bytes(b"def f():\n    return 2\n")
    (root / "b.py").write_bytes(b"import a\nraise RuntimeError('input must not run')\n")
    git("add", ".")
    git("commit", "-qm", "target")
    target = git("rev-parse", "HEAD")
    (root / "a.py").write_bytes(b"def broken(\n")
    git("add", ".")
    git("commit", "-qm", "broken")
    broken = git("rev-parse", "HEAD")
    (root / "a.py").write_bytes(b"DIRTY - must not parse or execute")
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    repo_id = "workflow-" + uuid4().hex
    settings = DatabaseSettings(
        URL.create(
            "postgresql+psycopg",
            username="smartregression_runtime",
            password=storage_context["runtime_password"],
            host="127.0.0.1",
            port=storage_context["port"],
            database="smartregression_kh_test",
            query={"sslmode": "disable"},
        ),
        allow_loopback_test=True,
    )
    # Only settings acquisition is injected for the dedicated harness loopback exception.
    # Production has no environment switch to disable TLS. Engine, Git, file and SQL are real.
    monkeypatch.setattr(
        "smartregression.adapters.storage.config.load_database_settings", lambda: settings
    )
    kwargs = dict(
        repository=root,
        repository_id=repo_id,
        authorized_root=root,
        base=base,
        target=target,
        data_kind="demo",
        artifact_root=artifact_root,
    )
    return kwargs, broken


@pytest.mark.parametrize("broken", [False, True])
def test_actual_cli_persists_partial_and_failed_stages(
    migrated, workflow_input, capsys, monkeypatch, broken
):
    owner, runtime, _ = migrated
    kwargs, broken_commit = workflow_input
    if broken:
        kwargs["target"] = broken_commit
    with owner.begin() as connection:
        connection.execute(
            repositories.insert().values(repository_id=kwargs["repository_id"], source_kind="local")
        )
    observed = []
    acquired_pairs = []
    acquire = composition.analyze_execution
    import smartregression.application.analysis as workflow
    from smartregression.application.evidence import inspect_bundle

    prepare = workflow.prepare_snapshots

    def observe_pair(*args, **kw):
        pair = prepare(*args, **kw)
        acquired_pairs.append(pair)
        return pair

    monkeypatch.setattr(workflow, "prepare_snapshots", observe_pair)

    def capture(*args, **kw):
        execution = acquire(*args, **kw)
        observed.append(execution)
        return execution

    monkeypatch.setattr(composition, "analyze_execution", capture)
    assert main(cli_arguments(kwargs)) == (2 if broken else 1)
    captured = capsys.readouterr()
    report = StageAnalysisReport.model_validate_json(captured.out)
    assert "Persistence saved" in captured.err
    assert report.analysis_status == "partial"
    assert report.stages.graph.status == ("failed" if broken else "completed")
    assert len(observed) == 1
    execution = observed[0]
    assert report == execution.report
    with runtime.connect() as connection:
        run = (
            connection.execute(
                sa.select(analysis_runs).where(
                    analysis_runs.c.repository_id == kwargs["repository_id"]
                )
            )
            .mappings()
            .one()
        )
        saved = (
            connection.execute(
                sa.select(run_reports).where(run_reports.c.repository_id == kwargs["repository_id"])
            )
            .mappings()
            .one()
        )
        artifact_row = (
            connection.execute(
                sa.select(artifacts).where(artifacts.c.repository_id == kwargs["repository_id"])
            )
            .mappings()
            .one()
        )
        stored_snapshots = (
            connection.execute(
                sa.select(snapshots).where(snapshots.c.repository_id == kwargs["repository_id"])
            )
            .mappings()
            .all()
        )
    assert run["configuration"] == json.loads(execution.configuration.canonical_bytes())
    assert (
        run["configuration_sha256"]
        == hashlib.sha256(execution.configuration.canonical_bytes()).hexdigest()
    )
    assert run["base_snapshot_id"] == report.identity.base.snapshot_id
    assert run["target_snapshot_id"] == report.identity.target.snapshot_id
    assert saved["stage_summary"]["graph"]["status"] == report.stages.graph.status
    assert saved["analysis_status"] == report.analysis_status
    assert saved["llm_cost_usd"] is None
    expected_bundle = bundle_from_report(report)
    loaded_bundle = PostgresEvidenceStore(runtime).load(report.identity)
    assert loaded_bundle == expected_bundle
    if expected_bundle is not None:
        assert prepare_evidence(loaded_bundle) == prepare_evidence(expected_bundle)
        before = prepare_evidence(loaded_bundle)
        assert inspect_bundle(loaded_bundle, acquired_pairs[0]).status == "completed"
        assert prepare_evidence(loaded_bundle) == before
        assert prepare_evidence(PostgresEvidenceStore(runtime).load(report.identity)) == before
        assert "evidence=saved" in captured.err
    else:
        assert "evidence=not_included_missing_stage_data" in captured.err
    assert {
        (
            row["commit_sha"],
            row["snapshot_id"],
            row["manifest_version"],
            row["materializer_version"],
        )
        for row in stored_snapshots
    } == {
        (m.commit, m.snapshot_id, m.schema_version, m.materializer_version)
        for m in execution.snapshot_manifests
    }
    descriptor = ReportArtifact(
        artifact_row["artifact_id"],
        artifact_row["storage_key"],
        artifact_row["sha256"],
        artifact_row["size_bytes"],
    )
    files = ReportFiles(kwargs["artifact_root"], source_repository=kwargs["repository"])
    assert (
        files.read(
            descriptor, expected_identity=report.identity, expected_report_id=report.report_id
        )
        == report
    )
    # Retry persistence of this exact execution, never run a fresh analyze as a retry.
    monkeypatch.setattr(composition, "analyze_execution", lambda *a, **k: execution)
    assert composition.analyze_local(**kwargs) == report
    changed = replace(
        execution, configuration=replace(execution.configuration, application_version="changed")
    )
    monkeypatch.setattr(composition, "analyze_execution", lambda *a, **k: changed)
    with pytest.raises(RunConflict):
        composition.analyze_local(**kwargs)
    with runtime.connect() as connection:
        assert (
            connection.scalar(
                sa.select(sa.func.count())
                .select_from(run_reports)
                .where(run_reports.c.repository_id == kwargs["repository_id"])
            )
            == 1
        )


def test_unprovisioned_repository_reports_failure_and_retains_orphan(
    migrated, workflow_input, capsys
):
    _, runtime, _ = migrated
    kwargs, _ = workflow_input
    assert main(cli_arguments(kwargs)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Persistence failed: run_storage_failed" in captured.err
    assert "Persistence saved" not in captured.err
    assert len(list(kwargs["artifact_root"].glob("*/*.json"))) == 1
    with runtime.connect() as connection:
        for table in (
            repositories,
            snapshots,
            analysis_runs,
            artifacts,
            run_reports,
            evidence_bundles,
        ):
            assert (
                connection.scalar(
                    sa.select(sa.func.count())
                    .select_from(table)
                    .where(table.c.repository_id == kwargs["repository_id"])
                )
                == 0
            )


def test_cli_bundle_write_failure_rolls_back_report_and_run(migrated, workflow_input, capsys):
    owner, runtime, _ = migrated
    kwargs, _ = workflow_input
    with owner.begin() as connection:
        connection.execute(
            repositories.insert().values(repository_id=kwargs["repository_id"], source_kind="local")
        )

    def fail_bundle(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO smartregression.evidence_bundles"):
            raise EvidenceStorageError()

    # Actual CLI creates its own engine, so instrument the SQL engine class for this
    # bounded test scope; never intercept credentials or SQL parameter values.
    sa.event.listen(sa.Engine, "before_cursor_execute", fail_bundle)
    try:
        assert main(cli_arguments(kwargs)) == 2
    finally:
        sa.event.remove(sa.Engine, "before_cursor_execute", fail_bundle)
    captured = capsys.readouterr()
    assert captured.out == "" and "Persistence failed: evidence_storage_failed" in captured.err
    assert "Persistence saved" not in captured.err
    assert len(list(kwargs["artifact_root"].glob("*/*.json"))) == 1
    with runtime.connect() as connection:
        for table in (snapshots, analysis_runs, artifacts, run_reports, evidence_bundles):
            assert (
                connection.scalar(
                    sa.select(sa.func.count())
                    .select_from(table)
                    .where(table.c.repository_id == kwargs["repository_id"])
                )
                == 0
            )


def test_existing_bundle_prevents_divergent_report_even_without_new_bundle(
    migrated,
    workflow_input,
    monkeypatch,
):
    from smartregression.application.analysis import aggregate_status
    from smartregression.application.evidence_store import EvidenceConflict
    from smartregression.contracts.stages import StageResult

    owner, _, _ = migrated
    kwargs, _ = workflow_input
    with owner.begin() as connection:
        connection.execute(
            repositories.insert().values(repository_id=kwargs["repository_id"], source_kind="local")
        )
    captured = []
    acquire = composition.analyze_execution

    def record(*args, **kw):
        execution = acquire(*args, **kw)
        captured.append(execution)
        return execution

    monkeypatch.setattr(composition, "analyze_execution", record)
    composition.analyze_local(**kwargs)
    execution = captured[0]
    graph = execution.report.stages.graph.data.model_copy(update={"edges": []})
    stages = execution.report.stages.model_copy(
        update={
            "graph": StageResult(status="completed", data=graph),
            "impact": StageResult(status="not_run", reason="dependency_failed"),
            "evidence": StageResult(status="not_run", reason="dependency_failed"),
            "review_ordering": StageResult(status="not_run", reason="dependency_failed"),
        }
    )
    report = execution.report.model_copy(
        update={
            "report_id": "different-report",
            "stages": stages,
            "analysis_status": aggregate_status(stages),
        }
    )
    monkeypatch.setattr(
        composition, "analyze_execution", lambda *a, **k: replace(execution, report=report)
    )
    with pytest.raises(EvidenceConflict):
        composition.analyze_local(**kwargs)

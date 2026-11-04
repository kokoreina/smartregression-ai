"""Actual CLI/composition -> frozen Git -> report file -> runtime-role PostgreSQL."""

import hashlib
import json
import subprocess
from dataclasses import replace
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import URL

import smartregression.composition as composition
from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.adapters.storage.schema import (
    analysis_runs,
    artifacts,
    repositories,
    run_reports,
    snapshots,
)
from smartregression.application.run_store import ReportArtifact, RunConflict
from smartregression.cli.main import main
from smartregression.contracts.stages import StageAnalysisReport


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
    acquire = composition.analyze_execution

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
        for table in (repositories, snapshots, analysis_runs, artifacts, run_reports):
            assert (
                connection.scalar(
                    sa.select(sa.func.count())
                    .select_from(table)
                    .where(table.c.repository_id == kwargs["repository_id"])
                )
                == 0
            )

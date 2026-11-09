"""Real PostgreSQL constraints/transactions; fixtures never point to a shared DB."""

import copy
import hashlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from conftest import alembic_config
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.schema import (
    analysis_runs,
    artifacts,
    metadata,
    repositories,
    run_reports,
    snapshots,
)
from smartregression.application.run_store import RunStorageError


def seed(connection, *, repository=None):
    repo = repository or "fixture-" + uuid4().hex
    connection.execute(repositories.insert().values(repository_id=repo, source_kind="local"))
    connection.execute(
        snapshots.insert(),
        [
            {
                "repository_id": repo,
                "commit_sha": c * 40,
                "snapshot_id": d * 64,
                "manifest_version": "snapshot/1",
                "materializer_version": "git-blobs/1",
            }
            for c, d in (("a", "c"), ("b", "d"))
        ],
    )
    run = dict(
        repository_id=repo,
        run_id="run-1",
        base_sha="a" * 40,
        target_sha="b" * 40,
        base_snapshot_id="c" * 64,
        target_snapshot_id="d" * 64,
        comparison_mode="direct_two_tree",
        data_kind="demo",
        configuration={},
        configuration_sha256=hashlib.sha256(b"{}\n").hexdigest(),
    )
    connection.execute(analysis_runs.insert().values(**run))
    return repo, run


def test_schema_matches_tables_and_upgrade_preserves_data(migrated):
    owner, _, _ = migrated
    with owner.connect() as connection:
        assert (
            connection.scalar(sa.text("SELECT version_num FROM smartregression.alembic_version"))
            == "20261109_06"
        )
        assert set(sa.inspect(connection).get_table_names(schema="smartregression")) == {
            "repositories",
            "snapshots",
            "analysis_runs",
            "artifacts",
            "run_reports",
            "run_stage_payloads",
            "evidence_bundles",
            "test_inventories",
            "test_cases",
            "knowledge_indexes",
            "index_chunks",
            "alembic_version",
        }
        context = MigrationContext.configure(
            connection,
            opts={
                "include_schemas": True,
                "include_object": lambda obj, name, kind, reflected, compare: (
                    name != "alembic_version"
                ),
            },
        )
        assert compare_metadata(context, metadata) == []


@pytest.mark.parametrize(
    "column,value",
    [
        ("base_snapshot_id", "e" * 64),
        ("target_sha", "e" * 40),
        ("comparison_mode", "merge_base"),
        ("configuration", []),
        ("configuration_sha256", "invalid"),
        ("run_id", "đ" * 257),
    ],
)
def test_invalid_run_values_rejected_and_transaction_rolls_back(migrated, column, value):
    owner, _, _ = migrated
    with owner.begin() as connection:
        _, row = seed(connection)
    row = {**row, "run_id": "bad-run", column: value}
    with pytest.raises(IntegrityError), owner.begin() as connection:
        connection.execute(analysis_runs.insert().values(**row))


def test_cross_repository_snapshot_reference_rejected(migrated):
    owner, _, _ = migrated
    with owner.begin() as connection:
        repo, _ = seed(connection)
        other = "other-" + uuid4().hex
        connection.execute(repositories.insert().values(repository_id=other, source_kind="local"))
    with pytest.raises(IntegrityError), owner.begin() as connection:
        connection.execute(
            analysis_runs.insert().values(
                repository_id=other,
                run_id="foreign",
                base_sha="a" * 40,
                target_sha="b" * 40,
                base_snapshot_id="c" * 64,
                target_snapshot_id="d" * 64,
                comparison_mode="direct_two_tree",
                data_kind="demo",
                configuration={},
                configuration_sha256="e" * 64,
            )
        )


def test_failure_run_can_keep_unknown_snapshot_hashes_without_fake_snapshots(migrated):
    owner, _, _ = migrated
    with owner.begin() as connection:
        repo = "failure-" + uuid4().hex
        connection.execute(repositories.insert().values(repository_id=repo, source_kind="local"))
        connection.execute(
            analysis_runs.insert().values(
                repository_id=repo,
                run_id="failed-acquisition",
                base_sha="a" * 40,
                target_sha="a" * 40,
                base_snapshot_id=None,
                target_snapshot_id=None,
                comparison_mode="direct_two_tree",
                data_kind="demo",
                configuration={},
                configuration_sha256="e" * 64,
            )
        )
        assert (
            connection.scalar(
                sa.select(sa.func.count())
                .select_from(snapshots)
                .where(snapshots.c.repository_id == repo)
            )
            == 0
        )


def test_real_h1_transaction_rolls_back_business_and_database_failures(migrated):
    owner, _, _ = migrated
    repo = "rollback-" + uuid4().hex
    with pytest.raises(RuntimeError, match="business"), database_transaction(owner) as connection:
        seed(connection, repository=repo)
        raise RuntimeError("business")
    with owner.connect() as connection:
        assert (
            connection.scalar(
                sa.select(sa.func.count())
                .select_from(repositories)
                .where(repositories.c.repository_id == repo)
            )
            == 0
        )
    with pytest.raises(RunStorageError), database_transaction(owner) as connection:
        connection.execute(sa.text("SELECT 1/0"))


@pytest.mark.parametrize(
    "statement",
    [
        "CREATE TABLE smartregression.denied (id int)",
        "ALTER TABLE smartregression.repositories ADD COLUMN denied int",
        "DROP TABLE smartregression.run_reports",
        "UPDATE smartregression.repositories SET source_kind='github'",
        "DELETE FROM smartregression.repositories",
        "CREATE TABLE public.denied (id int)",
    ],
)
def test_runtime_has_no_ddl_update_delete_privileges(migrated, statement):
    _, runtime, _ = migrated
    with pytest.raises(DBAPIError), runtime.begin() as connection:
        connection.execute(sa.text(statement))


def test_runtime_can_insert_and_read_fixture_metadata(migrated):
    _, runtime, _ = migrated
    with database_transaction(runtime) as connection:
        repo, _ = seed(connection)
        assert (
            connection.scalar(
                sa.select(repositories.c.source_kind).where(repositories.c.repository_id == repo)
            )
            == "local"
        )


@pytest.mark.parametrize("mutate", ["wrong_run", "missing_key", "null_status", "nan", "infinity"])
def test_report_scoping_shape_and_finite_metrics(migrated, stage_artifacts, mutate):
    owner, _, _ = migrated
    summary = {
        name: {k: v for k, v in value.items() if k != "data"}
        for name, value in stage_artifacts["stages"].items()
    }
    with owner.begin() as connection:
        repo, run = seed(connection)
        connection.execute(
            artifacts.insert().values(
                repository_id=repo,
                run_id=run["run_id"],
                artifact_id="report-file",
                storage_key="reports/" + uuid4().hex + ".json",
                kind="report_json",
                sha256="e" * 64,
                size_bytes=10,
                media_type="application/json",
                schema_version="2.0.0",
                access_class="repository",
            )
        )
    row = dict(
        repository_id=repo,
        run_id="run-1",
        report_id="report-1",
        artifact_id="report-file",
        schema_version="2.0.0",
        analysis_status="partial",
        stage_summary=copy.deepcopy(summary),
    )
    if mutate == "wrong_run":
        with owner.begin() as connection:
            connection.execute(analysis_runs.insert().values(**{**run, "run_id": "run-2"}))
        row["run_id"] = "run-2"
    elif mutate == "missing_key":
        row["stage_summary"].pop("inventory")
    elif mutate == "null_status":
        row["stage_summary"]["inventory"]["status"] = None
    else:
        row["analysis_duration_seconds"] = float("nan" if mutate == "nan" else "inf")
    with pytest.raises(IntegrityError), owner.begin() as connection:
        connection.execute(run_reports.insert().values(**row))


def test_failed_second_revision_is_atomic_and_can_retry(migrated):
    _, _, engine = migrated
    with engine.connect() as connection:
        command.upgrade(alembic_config(connection), "20261103_01")

    def fail_report_table(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().startswith("CREATE TABLE smartregression.run_reports"):
            raise RuntimeError("injected migration failure")

    sa.event.listen(engine, "before_cursor_execute", fail_report_table)
    try:
        with (
            pytest.raises(RuntimeError, match="injected migration failure"),
            engine.connect() as connection,
        ):
            command.upgrade(alembic_config(connection), "head")
    finally:
        sa.event.remove(engine, "before_cursor_execute", fail_report_table)
    with engine.connect() as connection:
        assert (
            connection.scalar(sa.text("SELECT version_num FROM smartregression.alembic_version"))
            == "20261103_01"
        )
        assert "artifacts" not in sa.inspect(connection).get_table_names(schema="smartregression")
    with engine.connect() as connection:
        command.upgrade(alembic_config(connection), "head")


def test_two_real_connections_arbitrate_same_unique_key(migrated):
    owner, _, _ = migrated
    repo = "concurrent-" + uuid4().hex
    barrier = Barrier(2)

    def write():
        with owner.begin() as connection:
            barrier.wait(timeout=5)
            return connection.execute(
                insert(repositories)
                .values(repository_id=repo, source_kind="local")
                .on_conflict_do_nothing()
                .returning(repositories.c.repository_id)
            ).scalar_one_or_none()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(write) for _ in range(2)]
        results = [future.result(timeout=15) for future in futures]
        assert results.count(repo) == 1 and results.count(None) == 1
    with owner.connect() as connection:
        assert (
            connection.scalar(
                sa.select(sa.func.count())
                .select_from(repositories)
                .where(repositories.c.repository_id == repo)
            )
            == 1
        )


def test_report_roundtrip_preserves_partial_status_summary_and_null_metrics(
    migrated, stage_artifacts
):
    owner, _, _ = migrated
    summary = {
        name: {k: v for k, v in value.items() if k != "data"}
        for name, value in stage_artifacts["stages"].items()
    }
    with owner.begin() as connection:
        repo, _ = seed(connection)
        connection.execute(
            artifacts.insert().values(
                repository_id=repo,
                artifact_id="file-1",
                run_id="run-1",
                storage_key="reports/" + uuid4().hex + ".json",
                kind="report_json",
                sha256="f" * 64,
                size_bytes=100,
                media_type="application/json",
                schema_version="2.0.0",
                access_class="repository",
            )
        )
        connection.execute(
            run_reports.insert().values(
                repository_id=repo,
                run_id="run-1",
                report_id="report-1",
                artifact_id="file-1",
                schema_version="2.0.0",
                analysis_status="partial",
                stage_summary=summary,
                analysis_duration_seconds=None,
                llm_cost_usd=None,
            )
        )
    with owner.connect() as connection:
        row = (
            connection.execute(sa.select(run_reports).where(run_reports.c.repository_id == repo))
            .mappings()
            .one()
        )
        assert row["stage_summary"] == summary
        assert row["analysis_status"] == "partial"
        assert row["analysis_duration_seconds"] is None and row["llm_cost_usd"] is None

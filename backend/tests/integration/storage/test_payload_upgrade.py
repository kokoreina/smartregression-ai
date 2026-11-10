"""Upgrade populated pre-ledger rows; never infer their payload hashes from status."""

import json
from dataclasses import asdict

import sqlalchemy as sa
from alembic import command
from conftest import alembic_config
from test_postgres_run_store import arguments

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine
from smartregression.adapters.storage.run_store import PostgresRunReportStore
from smartregression.adapters.storage.schema import (
    analysis_runs,
    artifacts,
    repositories,
    run_reports,
    run_stage_payloads,
    snapshots,
)
from smartregression.application.run_store import prepare_run_report


def test_populated_legacy_upgrade_preserves_exact_rows(migrated, stage_artifacts):
    owner, _, _ = migrated
    settings = DatabaseSettings(
        owner.url.set(database="smartregression_kh_legacy"), allow_loopback_test=True
    )
    write = prepare_run_report(**arguments(stage_artifacts))
    identity = write.identity
    scope = dict(repository_id=identity.repository_id, run_id=identity.run_id)
    tables = [repositories, snapshots, analysis_runs, artifacts, run_reports]
    with database_engine(settings) as engine:
        with engine.connect() as connection:
            command.upgrade(alembic_config(connection), "20261105_05")
        # Raw INSERTs are migration-fixture setup, not a claim that the current
        # report writer works against the older schema without its required head.
        with engine.begin() as connection:
            connection.execute(
                repositories.insert().values(
                    repository_id=identity.repository_id, source_kind="local"
                )
            )
            connection.execute(snapshots.insert(), [asdict(s) for s in write.snapshots])
            connection.execute(
                analysis_runs.insert().values(
                    **scope,
                    base_sha=identity.base.commit,
                    target_sha=identity.target.commit,
                    base_snapshot_id=identity.base.snapshot_id,
                    target_snapshot_id=identity.target.snapshot_id,
                    comparison_mode=identity.comparison_mode,
                    data_kind=write.data_kind,
                    configuration=json.loads(write.configuration_json),
                    configuration_sha256=write.configuration_sha256,
                )
            )
            connection.execute(
                artifacts.insert().values(
                    **scope,
                    **asdict(write.artifact),
                    kind="report_json",
                    media_type="application/json",
                    schema_version="2.0.0",
                    access_class="repository",
                )
            )
            connection.execute(
                run_reports.insert().values(
                    **scope,
                    report_id=write.report_id,
                    artifact_id=write.artifact.artifact_id,
                    schema_version="2.0.0",
                    analysis_status=write.analysis_status,
                    stage_summary=json.loads(write.stage_summary_json),
                    analysis_duration_seconds=write.analysis_duration_seconds,
                    llm_cost_usd=write.llm_cost_usd,
                )
            )
        with engine.begin() as connection:
            before = [connection.execute(sa.select(t)).mappings().all() for t in tables]
            command.upgrade(alembic_config(connection), "head")
            command.upgrade(alembic_config(connection), "head")
            assert before == [connection.execute(sa.select(t)).mappings().all() for t in tables]
            assert (
                connection.scalar(sa.select(sa.func.count()).select_from(run_stage_payloads)) == 0
            )
        # The exact immutable artifact/config/summary match permits this trusted
        # replay to claim its own payloads. It never updates historical rows.
        PostgresRunReportStore(engine).save(write)
        with engine.connect() as connection:
            assert before == [connection.execute(sa.select(t)).mappings().all() for t in tables]
            assert dict(
                connection.execute(
                    sa.select(run_stage_payloads.c.stage_name, run_stage_payloads.c.payload_sha256)
                ).all()
            ) == json.loads(write.payload_digests_json)

"""Atomic immutable run/report metadata on the five-table PostgreSQL foundation."""

import json
from dataclasses import asdict

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.payload_claims import claim_payloads
from smartregression.adapters.storage.schema import (
    analysis_runs,
    artifacts,
    repositories,
    run_reports,
    snapshots,
)
from smartregression.application.run_store import (
    RunConflict,
    RunReportWrite,
    RunStorageError,
    validate_run_report_write,
)


def _immutable_insert(connection: sa.Connection, table: sa.Table, values: dict) -> None:
    keys = {column.name: values[column.name] for column in table.primary_key}
    inserted = connection.execute(
        insert(table)
        .values(**values)
        .on_conflict_do_nothing()
        .returning(next(iter(table.primary_key)))
    ).scalar_one_or_none()
    if inserted is not None:
        return
    row = (
        connection.execute(
            sa.select(table).where(*[table.c[name] == value for name, value in keys.items()])
        )
        .mappings()
        .one_or_none()
    )
    if row is None or any(row[name] != value for name, value in values.items()):
        raise RunConflict()


class BoundRunReportStore:
    """Requires the caller's live transaction; never commits, rolls back or retries."""

    def __init__(self, connection: sa.Connection) -> None:
        self.connection = connection

    def save(self, write: RunReportWrite) -> None:
        write = validate_run_report_write(write)
        try:
            self._save(write)
        except sa.exc.SQLAlchemyError:
            raise RunStorageError() from None

    def _save(self, write: RunReportWrite) -> None:
        connection = self.connection
        if connection.closed or not connection.in_transaction():
            raise RunStorageError()
        identity = write.identity
        if (
            connection.scalar(
                sa.select(repositories.c.repository_id).where(
                    repositories.c.repository_id == identity.repository_id
                )
            )
            is None
        ):
            # Provisioning/authentication are upstream. A report cannot register a repo.
            raise RunStorageError()
        for snapshot in write.snapshots:
            _immutable_insert(connection, snapshots, asdict(snapshot))
        scope = {"repository_id": identity.repository_id, "run_id": identity.run_id}
        _immutable_insert(
            connection,
            analysis_runs,
            {
                **scope,
                "base_sha": identity.base.commit,
                "target_sha": identity.target.commit,
                "base_snapshot_id": identity.base.snapshot_id,
                "target_snapshot_id": identity.target.snapshot_id,
                "comparison_mode": identity.comparison_mode,
                "data_kind": write.data_kind,
                "configuration": json.loads(write.configuration_json),
                "configuration_sha256": write.configuration_sha256,
            },
        )
        _immutable_insert(
            connection,
            artifacts,
            {
                **scope,
                **asdict(write.artifact),
                "kind": "report_json",
                "media_type": "application/json",
                "schema_version": "2.0.0",
                "access_class": "repository",
            },
        )
        _immutable_insert(
            connection,
            run_reports,
            {
                **scope,
                "report_id": write.report_id,
                "artifact_id": write.artifact.artifact_id,
                "schema_version": "2.0.0",
                "analysis_status": write.analysis_status,
                "stage_summary": json.loads(write.stage_summary_json),
                "analysis_duration_seconds": write.analysis_duration_seconds,
                "llm_cost_usd": write.llm_cost_usd,
            },
        )
        claim_payloads(
            connection,
            identity,
            json.loads(write.payload_digests_json),
            verified_report_id=write.report_id,
        )


class PostgresRunReportStore:
    def __init__(self, engine: sa.Engine) -> None:
        self.engine = engine

    def save(self, write: RunReportWrite) -> None:
        # Reject unsupported metadata before acquiring any database connection.
        write = validate_run_report_write(write)
        with database_transaction(self.engine) as connection:
            BoundRunReportStore(connection).save(write)

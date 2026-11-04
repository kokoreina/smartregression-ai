"""Atomic immutable inventory/header rows using the existing transaction boundary."""

import json

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.schema import (
    analysis_runs,
    artifacts,
    test_cases,
    test_inventories,
)
from smartregression.application.inventory_store import (
    InventoryConfiguration,
    InventoryConflict,
    InventoryMetadataError,
    InventoryWrite,
    prepare_inventory,
    test_id_digest,
    validate_inventory_write,
)
from smartregression.application.run_store import RunStorageError
from smartregression.contracts.stages import InventoryPayload, RunIdentity, StageResult


def _scope(table, identity, inventory_id=None):
    conditions = [
        table.c.repository_id == identity.repository_id,
        table.c.run_id == identity.run_id,
    ]
    if inventory_id is not None:
        conditions.append(table.c.inventory_id == inventory_id)
    return conditions


def _header(write):
    identity, stage, config = write.identity, write.stage, write.configuration
    return dict(
        repository_id=identity.repository_id,
        run_id=identity.run_id,
        inventory_id=write.inventory_id,
        target_sha=identity.target.commit,
        target_snapshot_id=identity.target.snapshot_id,
        framework="pytest",
        collector_version=config.collector_version,
        image_id=config.image_id,
        configuration=json.loads(write.configuration_json),
        configuration_sha256=write.configuration_sha256,
        stage_status=stage.status,
        completeness=stage.data.completeness if stage.data else None,
        test_count=len(stage.data.test_ids) if stage.data else None,
        reason=stage.reason,
        error_code=stage.error_code,
        limitations=[item.model_dump(mode="json") for item in stage.limitations],
        exit_code=write.exit_code,
        duration_seconds=write.duration_seconds,
        diagnostic_artifact_id=write.diagnostic_artifact_id,
    )


class BoundInventoryStore:
    """Caller owns one live transaction; saving never provisions runs/snapshots."""

    def __init__(self, connection: sa.Connection):
        self.connection = connection

    def _run(self, identity):
        row = (
            self.connection.execute(
                sa.select(analysis_runs).where(*_scope(analysis_runs, identity))
            )
            .mappings()
            .one_or_none()
        )
        if row is None or any(
            row[key] != value
            for key, value in {
                "base_sha": identity.base.commit,
                "target_sha": identity.target.commit,
                "base_snapshot_id": identity.base.snapshot_id,
                "target_snapshot_id": identity.target.snapshot_id,
                "comparison_mode": identity.comparison_mode,
            }.items()
        ):
            raise InventoryConflict()

    def _ready(self):
        if self.connection.closed or not self.connection.in_transaction():
            raise RunStorageError()

    def save(self, write: InventoryWrite) -> None:
        write = validate_inventory_write(write)
        self._ready()
        try:
            self._run(write.identity)
            if write.diagnostic_artifact_id is not None:
                diagnostic = self.connection.execute(
                    sa.select(artifacts.c.kind).where(
                        *_scope(artifacts, write.identity),
                        artifacts.c.artifact_id == write.diagnostic_artifact_id,
                    )
                ).scalar_one_or_none()
                if diagnostic != "log":
                    raise InventoryMetadataError()
            rows = []
            seen = {}
            for ordinal, node_id in enumerate(
                write.stage.data.test_ids if write.stage.data else []
            ):
                digest = test_id_digest(node_id)
                if digest in seen:
                    # Compare exact native text; a technical hash is never identity proof.
                    raise InventoryConflict()
                seen[digest] = node_id
                rows.append(
                    dict(
                        repository_id=write.identity.repository_id,
                        run_id=write.identity.run_id,
                        inventory_id=write.inventory_id,
                        test_id_sha256=digest,
                        test_id=node_id,
                        ordinal=ordinal,
                    )
                )
            inserted = self.connection.execute(
                insert(test_inventories)
                .values(**_header(write))
                .on_conflict_do_nothing()
                .returning(test_inventories.c.inventory_id)
            ).scalar_one_or_none()
            if inserted is None:
                old = self.load(write.identity, write.inventory_id, write.configuration_sha256)
                if old != write:
                    raise InventoryConflict()
                return
            if rows:
                self.connection.execute(test_cases.insert(), rows)
        except sa.exc.SQLAlchemyError:
            raise RunStorageError() from None

    def load(
        self, identity: RunIdentity, inventory_id: str, configuration_sha256: str
    ) -> InventoryWrite | None:
        self._ready()
        try:
            identity = RunIdentity.model_validate(identity.model_dump())
            self._run(identity)
            row = (
                self.connection.execute(
                    sa.select(test_inventories).where(
                        *_scope(test_inventories, identity, inventory_id)
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            if (row["target_sha"], row["target_snapshot_id"], row["configuration_sha256"]) != (
                identity.target.commit,
                identity.target.snapshot_id,
                configuration_sha256,
            ):
                raise InventoryConflict()
            cases = (
                self.connection.execute(
                    sa.select(test_cases)
                    .where(*_scope(test_cases, identity, inventory_id))
                    .order_by(test_cases.c.ordinal)
                )
                .mappings()
                .all()
            )
            for ordinal, case in enumerate(cases):
                if (
                    case["ordinal"] != ordinal
                    or test_id_digest(case["test_id"]) != case["test_id_sha256"]
                ):
                    raise InventoryMetadataError()
            ids = [case["test_id"] for case in cases]
            active = row["stage_status"] in {"completed", "partial"}
            if row["test_count"] != (len(ids) if active else None) or (not active and ids):
                raise InventoryMetadataError()
            stage = StageResult[InventoryPayload].model_validate(
                dict(
                    status=row["stage_status"],
                    reason=row["reason"],
                    error_code=row["error_code"],
                    limitations=row["limitations"],
                    data=dict(
                        snapshot=identity.target,
                        framework=row["framework"],
                        test_ids=ids,
                        completeness=row["completeness"],
                    )
                    if active
                    else None,
                )
            )
            config = dict(row["configuration"])
            config["plugins"] = tuple(config["plugins"])
            config = InventoryConfiguration(**config)
            if (
                (config.digest, config.collector_version, config.image_id)
                != (
                    row["configuration_sha256"],
                    row["collector_version"],
                    row["image_id"],
                )
                or row["framework"] != "pytest"
                or (not active and row["completeness"] is not None)
            ):
                raise InventoryMetadataError()
            return prepare_inventory(
                identity=identity,
                inventory_id=inventory_id,
                stage=stage,
                configuration=config,
                exit_code=row["exit_code"],
                duration_seconds=row["duration_seconds"],
                diagnostic_artifact_id=row["diagnostic_artifact_id"],
            )
        except sa.exc.SQLAlchemyError:
            raise RunStorageError() from None
        except ValueError, TypeError, KeyError, AttributeError:
            raise InventoryMetadataError() from None


class PostgresInventoryStore:
    def __init__(self, engine: sa.Engine):
        self.engine = engine

    def save(self, write: InventoryWrite) -> None:
        write = validate_inventory_write(write)
        with database_transaction(self.engine) as connection:
            BoundInventoryStore(connection).save(write)

    def load(
        self, identity: RunIdentity, inventory_id: str, configuration_sha256: str
    ) -> InventoryWrite | None:
        with database_transaction(self.engine) as connection:
            return BoundInventoryStore(connection).load(
                identity, inventory_id, configuration_sha256
            )

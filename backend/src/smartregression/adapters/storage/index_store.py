"""PostgreSQL index state transitions with scoped uniqueness and explicit attempts."""

import re

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.schema import index_chunks, knowledge_indexes, snapshots
from smartregression.application.index_store import (
    IndexBusy,
    IndexConflict,
    IndexCorrupt,
    IndexKey,
    IndexRecord,
    IndexStorageError,
    StoredIndex,
    decode_index_record,
    record_value,
    validate_attempt,
)
from smartregression.application.run_store import RunStorageError


def scope(key: IndexKey) -> list:
    key.__post_init__()
    return [
        knowledge_indexes.c.repository_id == key.repository_id,
        knowledge_indexes.c.commit_sha == key.commit,
        knowledge_indexes.c.snapshot_id == key.snapshot_id,
        knowledge_indexes.c.index_version == key.index_version,
        knowledge_indexes.c.configuration_sha256 == key.configuration_sha256,
    ]


def chunk_rows(record: IndexRecord) -> list[dict]:
    return [
        dict(
            repository_id=record.key.repository_id,
            index_id=record.manifest.index_id,
            chunk_id=c.chunk_id,
            ordinal=i,
            path=c.path,
            line_start=c.line_start,
            line_end=c.line_end,
            content_sha256=c.content_sha256,
            size_bytes=size,
        )
        for i, (c, size) in enumerate(zip(record.manifest.chunks, record.chunk_sizes, strict=True))
    ]


class BoundIndexStore:
    def __init__(self, connection: sa.Connection):
        self.connection = connection

    def load(self, key: IndexKey, *, lock: bool = False) -> StoredIndex | None:
        if self.connection.closed or not self.connection.in_transaction():
            raise IndexStorageError()
        query = sa.select(knowledge_indexes).where(*scope(key))
        row = (
            self.connection.execute(query.with_for_update() if lock else query)
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        record = decode_index_record(row["record"])
        validate_attempt(row["attempt_id"])
        if (
            record.key != key
            or record.manifest.index_id != row["index_id"]
            or row["backend"] != "local-lexical"
            or row["embedding_model"] is not None
            or row["state"] not in {"building", "ready", "failed"}
        ):
            raise IndexCorrupt()
        actual = (
            self.connection.execute(
                sa.select(index_chunks)
                .where(
                    index_chunks.c.repository_id == key.repository_id,
                    index_chunks.c.index_id == record.manifest.index_id,
                )
                .order_by(index_chunks.c.ordinal)
            )
            .mappings()
            .all()
        )
        if [dict(r) for r in actual] != chunk_rows(record):
            raise IndexCorrupt()
        return StoredIndex(record, row["state"], row["attempt_id"], row["error_code"])

    def begin(self, record: IndexRecord, attempt_id: str) -> StoredIndex:
        record.validate()
        validate_attempt(attempt_id)
        if self.connection.closed or not self.connection.in_transaction():
            raise IndexStorageError()
        key = record.key
        # Repositories are provisioned explicitly by composition, never by input data.
        snapshot_values = dict(
            repository_id=key.repository_id,
            commit_sha=key.commit,
            snapshot_id=key.snapshot_id,
            manifest_version=record.snapshot_version,
            materializer_version=record.materializer_version,
        )
        self.connection.execute(
            insert(snapshots).values(**snapshot_values).on_conflict_do_nothing()
        )
        snapshot = (
            self.connection.execute(
                sa.select(snapshots).where(
                    snapshots.c.repository_id == key.repository_id,
                    snapshots.c.commit_sha == key.commit,
                    snapshots.c.snapshot_id == key.snapshot_id,
                )
            )
            .mappings()
            .one()
        )
        if any(snapshot[k] != v for k, v in snapshot_values.items()):
            raise IndexConflict()
        inserted = self.connection.execute(
            insert(knowledge_indexes)
            .values(
                repository_id=key.repository_id,
                commit_sha=key.commit,
                snapshot_id=key.snapshot_id,
                index_version=key.index_version,
                configuration_sha256=key.configuration_sha256,
                index_id=record.manifest.index_id,
                backend="local-lexical",
                embedding_model=None,
                record=record_value(record),
                state="building",
                attempt_id=attempt_id,
            )
            .on_conflict_do_nothing()
            .returning(knowledge_indexes.c.index_id)
        ).scalar_one_or_none()
        if inserted is not None:
            rows = chunk_rows(record)
            if rows:
                self.connection.execute(index_chunks.insert(), rows)
        stored = self.load(key, lock=True)
        if stored is None or stored.record != record:
            raise IndexConflict()
        if stored.state == "ready":
            return stored
        if stored.state == "building" and stored.attempt_id != attempt_id:
            raise IndexBusy()
        if stored.state == "failed":
            self.connection.execute(
                knowledge_indexes.update()
                .where(*scope(key))
                .values(
                    state="building",
                    attempt_id=attempt_id,
                    error_code=None,
                )
            )
        return StoredIndex(record, "building", attempt_id)

    def finish(self, record: IndexRecord, attempt_id: str, error_code: str | None = None) -> None:
        record.validate()
        validate_attempt(attempt_id)
        if error_code is not None and not re.fullmatch(r"[a-z][a-z0-9_]{0,127}", error_code):
            raise ValueError("invalid_index_error_code")
        stored = self.load(record.key, lock=True)
        if stored is None or stored.record != record:
            raise IndexConflict()
        if stored.state == "ready" and error_code is None:
            return
        if stored.state != "building" or stored.attempt_id != attempt_id:
            raise IndexConflict()
        self.connection.execute(
            knowledge_indexes.update()
            .where(*scope(record.key))
            .values(
                state="ready" if error_code is None else "failed",
                error_code=error_code,
            )
        )


class PostgresIndexStore:
    def __init__(self, engine: sa.Engine):
        self.engine = engine

    def _call(self, method: str, *args):
        try:
            with database_transaction(self.engine) as connection:
                return getattr(BoundIndexStore(connection), method)(*args)
        except RunStorageError:
            raise IndexStorageError() from None
        except sa.exc.SQLAlchemyError:
            raise IndexStorageError() from None

    def begin(self, record: IndexRecord, attempt_id: str) -> StoredIndex:
        record.validate()
        validate_attempt(attempt_id)
        return self._call("begin", record, attempt_id)

    def finish(self, record: IndexRecord, attempt_id: str, error_code: str | None = None) -> None:
        return self._call("finish", record, attempt_id, error_code)

    def load(self, key: IndexKey) -> StoredIndex | None:
        key.__post_init__()
        return self._call("load", key)

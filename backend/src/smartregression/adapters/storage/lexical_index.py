"""Verified local artifacts and PostgreSQL lifecycle for deterministic P5 indexes."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from time import monotonic
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine, database_transaction
from smartregression.adapters.storage.report_publication import MAX_REPORT_BYTES, ReportFiles
from smartregression.adapters.storage.schema import knowledge_chunks, knowledge_indexes, snapshots
from smartregression.application.run_store import ReportArtifact, RunStorageError
from smartregression.core.git.snapshots import FrozenSnapshot, canonical_json
from smartregression.core.retrieval.lexical import (
    INDEX_VERSION,
    LexicalConfig,
    LexicalPlan,
    build_lexical_plan,
)


class IndexStorageError(RunStorageError):
    code = "index_storage_failed"


class IndexCorrupt(IndexStorageError):
    code = "index_storage_corrupt"


class IndexNotReady(IndexStorageError):
    code = "index_not_ready"


class IndexBuildTimeout(IndexStorageError):
    code = "lexical_build_timeout"


class IndexFiles:
    """Reuse guarded immutable publication, without cataloging chunks as reports."""

    def __init__(self, root: Path, *, source_repository: Path) -> None:
        self.files = ReportFiles(root, source_repository=source_repository)

    def _packed(self, plan: LexicalPlan):
        manifest = plan.manifest
        namespace = hashlib.sha256(manifest.repository_id.encode("utf-8")).hexdigest()
        prefix = f"indexes/{namespace}/{manifest.snapshot_id}/{plan.config.digest}"
        raw = plan.artifact_bytes()
        values = plan.chunks_by_range
        packs, positions = [], []
        current = bytearray()
        for chunk in manifest.chunks:
            content = values[(chunk.path, chunk.line_start, chunk.line_end)].source.content
            if current and len(current) + len(content) > MAX_REPORT_BYTES:
                packs.append(bytes(current))
                current.clear()
            positions.append(len(packs))
            current.extend(content)
        if current:
            packs.append(bytes(current))
        artifacts = [
            ReportArtifact(
                manifest.index_id,
                f"{prefix}/pack-{i}-{hashlib.sha256(content).hexdigest()}.bin",
                hashlib.sha256(content).hexdigest(),
                len(content),
            )
            for i, content in enumerate(packs)
        ]
        descriptor = ReportArtifact(
            manifest.index_id,
            f"{prefix}/{manifest.index_id}.json",
            hashlib.sha256(raw).hexdigest(),
            len(raw),
        )
        return (
            descriptor,
            [artifacts[p] for p in positions],
            list(zip(artifacts, packs, strict=True)),
        )

    def descriptors(self, plan: LexicalPlan) -> tuple[ReportArtifact, list[ReportArtifact]]:
        manifest, chunks, _ = self._packed(plan)
        return manifest, chunks

    def publish(self, plan: LexicalPlan) -> None:
        manifest, _, packs = self._packed(plan)
        for artifact, raw in packs:
            self.files.publish(artifact, raw)
        # Complete manifest is published last. A file alone is never a ready SQL index.
        self.files.publish(manifest, plan.artifact_bytes())

    def verify(self, plan: LexicalPlan) -> None:
        manifest, _, packs = self._packed(plan)
        if self.files.read_bytes(manifest) != plan.artifact_bytes():
            raise IndexCorrupt()
        for artifact, raw in packs:
            if self.files.read_bytes(artifact) != raw:
                raise IndexCorrupt()


def index_values(plan: LexicalPlan, files: IndexFiles, attempt: str) -> dict:
    artifact, _ = files.descriptors(plan)
    manifest = plan.manifest
    return dict(
        repository_id=manifest.repository_id,
        index_id=manifest.index_id,
        commit_sha=manifest.commit,
        snapshot_id=manifest.snapshot_id,
        configuration_id=plan.config.digest,
        configuration=json.loads(canonical_json(asdict(plan.config))),
        index_version=INDEX_VERSION,
        backend_kind="lexical",
        embedding_model=None,
        state="building",
        attempt_id=attempt,
        error_code=None,
        manifest_key=artifact.storage_key,
        manifest_sha256=artifact.sha256,
        manifest_bytes=artifact.size_bytes,
        chunk_count=len(manifest.chunks),
        content_bytes=sum(len(c.source.content) for c in plan.chunks),
    )


def chunk_values(plan: LexicalPlan, files: IndexFiles) -> list[dict]:
    _, descriptors = files.descriptors(plan)
    values = plan.chunks_by_range
    return [
        dict(
            repository_id=plan.manifest.repository_id,
            index_id=plan.manifest.index_id,
            chunk_id=c.chunk_id,
            path=c.path,
            line_start=c.line_start,
            line_end=c.line_end,
            symbol=values[(c.path, c.line_start, c.line_end)].symbol,
            content_sha256=c.content_sha256,
            content_key=artifact.storage_key,
            content_bytes=len(values[(c.path, c.line_start, c.line_end)].source.content),
        )
        for c, artifact in zip(plan.manifest.chunks, descriptors, strict=True)
    ]


def _scope(plan: LexicalPlan):
    return (
        knowledge_indexes.c.repository_id == plan.manifest.repository_id,
        knowledge_indexes.c.index_id == plan.manifest.index_id,
    )


def _check_metadata(row, expected: dict) -> None:
    mutable = {"state", "attempt_id", "error_code"}
    if any(row[key] != value for key, value in expected.items() if key not in mutable):
        raise IndexCorrupt()


def _check_chunks(connection: sa.Connection, plan: LexicalPlan, files: IndexFiles) -> None:
    rows = (
        connection.execute(
            sa.select(knowledge_chunks).where(
                knowledge_chunks.c.repository_id == plan.manifest.repository_id,
                knowledge_chunks.c.index_id == plan.manifest.index_id,
            )
        )
        .mappings()
        .all()
    )
    expected = chunk_values(plan, files)
    if sorted((dict(r) for r in rows), key=lambda r: r["chunk_id"]) != sorted(
        expected, key=lambda r: r["chunk_id"]
    ):
        raise IndexCorrupt()


class PostgresLexicalStore:
    """Caller authorizes/acquires sources. No repository provisioning or retries.

    Recompute expected deterministic plan from actual acquired bytes when loading;
    compare artifact bytes and every SQL chunk descriptor, never a ready boolean.
    Published artifacts survive SQL failures/ambiguous commits for reconciliation.
    """

    def __init__(self, engine: sa.Engine, files: IndexFiles) -> None:
        self.engine, self.files = engine, files

    def _load(self, plan: LexicalPlan) -> LexicalPlan | None:
        with database_transaction(self.engine) as connection:
            row = (
                connection.execute(sa.select(knowledge_indexes).where(*_scope(plan)))
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            _check_metadata(row, index_values(plan, self.files, row["attempt_id"]))
            if row["state"] != "ready":
                raise IndexNotReady()
            _check_chunks(connection, plan, self.files)
        self.files.verify(plan)
        return plan

    def load(self, snapshot: FrozenSnapshot, config: LexicalConfig) -> LexicalPlan | None:
        plan = build_lexical_plan(snapshot, config)
        try:
            return self._load(plan)
        except IndexStorageError:
            raise
        except RunStorageError, sa.exc.SQLAlchemyError, OSError:
            raise IndexStorageError() from None

    def ensure(self, snapshot: FrozenSnapshot, config: LexicalConfig) -> LexicalPlan:
        deadline = monotonic() + config.build_seconds
        plan = build_lexical_plan(snapshot, config)
        attempt = uuid4().hex
        expected = index_values(plan, self.files, attempt)
        try:
            with database_transaction(self.engine) as connection:
                manifest = snapshot.manifest
                # Repository must be provisioned explicitly. Register only verified
                # acquisition metadata; source rows grant no authorization.
                connection.execute(
                    insert(snapshots)
                    .values(
                        repository_id=manifest.repository_id,
                        commit_sha=manifest.commit,
                        snapshot_id=manifest.snapshot_id,
                        manifest_version=manifest.schema_version,
                        materializer_version=manifest.materializer_version,
                    )
                    .on_conflict_do_nothing()
                )
                stored_snapshot = (
                    connection.execute(
                        sa.select(snapshots).where(
                            snapshots.c.repository_id == manifest.repository_id,
                            snapshots.c.commit_sha == manifest.commit,
                            snapshots.c.snapshot_id == manifest.snapshot_id,
                        )
                    )
                    .mappings()
                    .one()
                )
                if (
                    stored_snapshot["manifest_version"] != manifest.schema_version
                    or stored_snapshot["materializer_version"] != manifest.materializer_version
                ):
                    raise IndexCorrupt()
                connection.execute(
                    insert(knowledge_indexes).values(**expected).on_conflict_do_nothing()
                )
                row = (
                    connection.execute(sa.select(knowledge_indexes).where(*_scope(plan)))
                    .mappings()
                    .one()
                )
                _check_metadata(row, expected)
                state = row["state"]
                if state == "failed":
                    connection.execute(
                        knowledge_indexes.update()
                        .where(*_scope(plan), knowledge_indexes.c.state == "failed")
                        .values(
                            state="building",
                            error_code=None,
                            attempt_id=attempt,
                            updated_at=sa.func.current_timestamp(),
                        )
                    )
            if state == "ready":
                ready = self._load(plan)
                if ready is None:
                    raise IndexCorrupt()
                return ready
            self.files.publish(plan)
            self.files.verify(plan)
            if monotonic() >= deadline:
                raise IndexBuildTimeout()
            with database_transaction(self.engine) as connection:
                row = (
                    connection.execute(
                        sa.select(knowledge_indexes).where(*_scope(plan)).with_for_update()
                    )
                    .mappings()
                    .one()
                )
                _check_metadata(row, expected)
                if row["state"] == "building":
                    values = chunk_values(plan, self.files)
                    # Keep parameter counts below PostgreSQL's protocol cap at
                    # the accepted 10,000-chunk limit; all batches share one tx.
                    for start in range(0, len(values), 500):
                        connection.execute(
                            insert(knowledge_chunks)
                            .values(values[start : start + 500])
                            .on_conflict_do_nothing()
                        )
                    _check_chunks(connection, plan, self.files)
                    connection.execute(
                        knowledge_indexes.update()
                        .where(*_scope(plan))
                        .values(
                            state="ready", error_code=None, updated_at=sa.func.current_timestamp()
                        )
                    )
                elif row["state"] != "ready":
                    raise IndexNotReady()
                _check_chunks(connection, plan, self.files)
                if monotonic() >= deadline:
                    raise IndexBuildTimeout()
            ready = self._load(plan)
            if ready is None:
                raise IndexCorrupt()
            return ready
        except (RunStorageError, sa.exc.SQLAlchemyError, OSError) as exc:
            # Best-effort diagnostics for only this attempt. Never overwrite ready,
            # delete artifacts, replay a build, or hide an ambiguous commit.
            try:
                with database_transaction(self.engine) as connection:
                    connection.execute(
                        knowledge_indexes.update()
                        .where(
                            *_scope(plan),
                            knowledge_indexes.c.state == "building",
                            knowledge_indexes.c.attempt_id == attempt,
                        )
                        .values(
                            state="failed",
                            error_code=(
                                exc.code
                                if isinstance(exc, IndexStorageError)
                                else "index_storage_failed"
                            ),
                            updated_at=sa.func.current_timestamp(),
                        )
                    )
            except RunStorageError, sa.exc.SQLAlchemyError:
                pass
            if isinstance(exc, IndexStorageError):
                raise
            raise IndexStorageError() from None


class ConfiguredLexicalStore:
    """Composition adapter: open scoped engines lazily after source authorization."""

    def __init__(self, settings: DatabaseSettings, files: IndexFiles) -> None:
        self.settings, self.files = settings, files

    def ensure(self, snapshot: FrozenSnapshot, config: LexicalConfig) -> LexicalPlan:
        with database_engine(self.settings) as engine:
            return PostgresLexicalStore(engine, self.files).ensure(snapshot, config)

    def load(self, snapshot: FrozenSnapshot, config: LexicalConfig) -> LexicalPlan | None:
        with database_engine(self.settings) as engine:
            return PostgresLexicalStore(engine, self.files).load(snapshot, config)

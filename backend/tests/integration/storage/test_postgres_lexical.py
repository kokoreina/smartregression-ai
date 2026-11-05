"""Real PostgreSQL + immutable artifact lifecycle; sources are owned static fixtures."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from threading import Barrier
from uuid import uuid4

import pytest
import sqlalchemy as sa

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.lexical_index import (
    IndexFiles,
    IndexNotReady,
    IndexStorageError,
    PostgresLexicalStore,
)
from smartregression.adapters.storage.schema import (
    knowledge_chunks,
    knowledge_indexes,
    repositories,
)
from smartregression.application.run_store import RunStorageError
from smartregression.core.git.snapshots import TreeEntry, freeze_snapshot
from smartregression.core.retrieval.lexical import LexicalConfig, search_lexical


@pytest.fixture
def lexical(migrated, tmp_path):
    owner, runtime, _ = migrated
    repo_id = "lexical-" + uuid4().hex
    content = b"def calcValue():\r\n    return 1\r\n"
    blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    snapshot = freeze_snapshot(
        repo_id, "a" * 40, (TreeEntry("calc.py", "100644", blob, len(content)),), (content,)
    )
    source, root = tmp_path / "source", tmp_path / "artifacts"
    source.mkdir()
    root.mkdir()
    with owner.begin() as connection:
        connection.execute(repositories.insert().values(repository_id=repo_id, source_kind="local"))
    files = IndexFiles(root, source_repository=source)
    return owner, runtime, snapshot, files, LexicalConfig()


def test_ready_roundtrip_reuse_and_configuration_scoping(lexical):
    owner, runtime, snapshot, files, config = lexical
    store = PostgresLexicalStore(runtime, files)
    assert store.load(snapshot, config) is None
    plan = store.ensure(snapshot, config)
    assert store.load(snapshot, config) == plan
    assert store.ensure(snapshot, config) == plan
    assert search_lexical(plan, snapshot, terms=("calc",)).data.items
    new_config = replace(config, chunk_lines=1)
    assert store.load(snapshot, new_config) is None
    new = store.ensure(snapshot, new_config)
    assert new.manifest.index_id != plan.manifest.index_id
    with owner.connect() as connection:
        rows = (
            connection.execute(
                sa.select(knowledge_indexes).where(
                    knowledge_indexes.c.repository_id == snapshot.manifest.repository_id
                )
            )
            .mappings()
            .all()
        )
    assert len(rows) == 2
    assert all(r["state"] == "ready" and r["embedding_model"] is None for r in rows)


@pytest.mark.parametrize("kind", ["content", "manifest", "metadata", "missing_chunk"])
def test_ready_index_is_verified_on_every_persisted_read(lexical, kind):
    owner, runtime, snapshot, files, config = lexical
    store = PostgresLexicalStore(runtime, files)
    plan = store.ensure(snapshot, config)
    manifest, chunks = files.descriptors(plan)
    if kind in {"content", "manifest"}:
        descriptor = chunks[0] if kind == "content" else manifest
        (files.files.root / descriptor.storage_key).write_bytes(b"tampered")
    else:
        with owner.begin() as connection:
            statement = (
                knowledge_chunks.delete()
                if kind == "missing_chunk"
                else knowledge_chunks.update().values(line_end=99)
            )
            connection.execute(
                statement.where(knowledge_chunks.c.repository_id == snapshot.manifest.repository_id)
            )
    with pytest.raises(IndexStorageError):
        store.load(snapshot, config)
    with pytest.raises(IndexStorageError):
        store.ensure(snapshot, config)  # Never rebuild over corrupt ready artifacts.


def test_publication_failure_never_creates_ready_and_failed_attempt_is_retryable(
    lexical, monkeypatch
):
    owner, runtime, snapshot, files, config = lexical
    store = PostgresLexicalStore(runtime, files)
    original = files.publish

    def fail(plan):
        raise RunStorageError()

    monkeypatch.setattr(files, "publish", fail)
    with pytest.raises(IndexStorageError):
        store.ensure(snapshot, config)
    with owner.connect() as connection:
        assert (
            connection.scalar(
                sa.select(knowledge_indexes.c.state).where(
                    knowledge_indexes.c.repository_id == snapshot.manifest.repository_id
                )
            )
            == "failed"
        )
    with pytest.raises(IndexNotReady):
        store.load(snapshot, config)
    monkeypatch.setattr(files, "publish", original)
    assert store.ensure(snapshot, config).manifest


def test_lost_commit_ack_is_not_replayed_or_deleted(lexical, monkeypatch):
    _, runtime, snapshot, files, config = lexical
    import smartregression.adapters.storage.lexical_index as storage

    count = 0

    @contextmanager
    def lost_ack(engine):
        nonlocal count
        count += 1
        with database_transaction(engine) as connection:
            yield connection
        if count == 2:  # Ready transaction reached server; response is lost.
            raise RunStorageError()

    with monkeypatch.context() as patch:
        patch.setattr(storage, "database_transaction", lost_ack)
        with pytest.raises(IndexStorageError):
            PostgresLexicalStore(runtime, files).ensure(snapshot, config)
    plan = PostgresLexicalStore(runtime, files).load(snapshot, config)
    assert plan is not None
    files.verify(plan)


def test_concurrent_builds_share_one_verified_ready_index(lexical):
    owner, runtime, snapshot, files, config = lexical
    gate = Barrier(2)

    def build(_):
        gate.wait(timeout=5)
        return PostgresLexicalStore(runtime, files).ensure(snapshot, config)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.map(build, range(2))
    assert first == second
    with owner.connect() as connection:
        assert (
            connection.scalar(
                sa.select(sa.func.count())
                .select_from(knowledge_indexes)
                .where(knowledge_indexes.c.repository_id == snapshot.manifest.repository_id)
            )
            == 1
        )


def test_ready_metadata_is_immutable_and_runtime_cannot_change_identity(lexical):
    _, runtime, snapshot, files, config = lexical
    PostgresLexicalStore(runtime, files).ensure(snapshot, config)
    with pytest.raises(RunStorageError), database_transaction(runtime) as connection:
        connection.execute(
            knowledge_indexes.update()
            .where(knowledge_indexes.c.repository_id == snapshot.manifest.repository_id)
            .values(state="building")
        )
    with pytest.raises(RunStorageError), database_transaction(runtime) as connection:
        connection.execute(
            knowledge_indexes.update()
            .where(knowledge_indexes.c.repository_id == snapshot.manifest.repository_id)
            .values(commit_sha="b" * 40)
        )


def test_timeout_after_publication_records_failed_without_ready(lexical, monkeypatch):
    owner, runtime, snapshot, files, config = lexical
    ticks = iter([0, 61])
    monkeypatch.setattr(
        "smartregression.adapters.storage.lexical_index.monotonic", lambda: next(ticks)
    )
    with pytest.raises(IndexStorageError, match="lexical_build_timeout"):
        PostgresLexicalStore(runtime, files).ensure(snapshot, config)
    with owner.connect() as connection:
        row = (
            connection.execute(
                sa.select(knowledge_indexes).where(
                    knowledge_indexes.c.repository_id == snapshot.manifest.repository_id
                )
            )
            .mappings()
            .one()
        )
    assert row["state"] == "failed" and row["error_code"] == "lexical_build_timeout"
    assert (files.files.root / row["manifest_key"]).exists()


def test_sql_failure_after_artifact_publish_preserves_orphan_and_reconciles(lexical, monkeypatch):
    owner, runtime, snapshot, files, config = lexical
    import smartregression.adapters.storage.lexical_index as storage

    calls = 0

    @contextmanager
    def fail_ready_transaction(engine):
        nonlocal calls
        calls += 1
        with database_transaction(engine) as connection:
            yield connection
            if calls == 2:
                raise RunStorageError()  # Roll back chunks and ready together.

    with monkeypatch.context() as patch:
        patch.setattr(storage, "database_transaction", fail_ready_transaction)
        with pytest.raises(IndexStorageError):
            PostgresLexicalStore(runtime, files).ensure(snapshot, config)
    with owner.connect() as connection:
        row = (
            connection.execute(
                sa.select(knowledge_indexes).where(
                    knowledge_indexes.c.repository_id == snapshot.manifest.repository_id
                )
            )
            .mappings()
            .one()
        )
        assert (
            connection.scalar(
                sa.select(sa.func.count())
                .select_from(knowledge_chunks)
                .where(knowledge_chunks.c.repository_id == snapshot.manifest.repository_id)
            )
            == 0
        )
    assert row["state"] == "failed"
    assert (files.files.root / row["manifest_key"]).exists()
    plan = PostgresLexicalStore(runtime, files).ensure(snapshot, config)
    files.verify(plan)


def test_accepted_chunk_cap_roundtrips_without_postgresql_parameter_overflow(lexical):
    _, runtime, original, files, config = lexical
    content = b"alpha\n" * 10_000
    blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    snapshot = freeze_snapshot(
        original.manifest.repository_id,
        "b" * 40,
        (TreeEntry("large.md", "100644", blob, len(content)),),
        (content,),
    )
    config = replace(config, chunk_lines=1)
    store = PostgresLexicalStore(runtime, files)
    plan = store.ensure(snapshot, config)
    assert len(plan.chunks) == 10_000
    assert store.load(snapshot, config) == plan

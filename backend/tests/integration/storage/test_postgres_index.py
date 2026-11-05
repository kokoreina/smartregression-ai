"""Actual Git, guarded artifacts and PostgreSQL; only dedicated labelled test DB."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from smartregression.adapters.storage.index_artifacts import IndexArtifactFiles
from smartregression.adapters.storage.index_store import BoundIndexStore, PostgresIndexStore, scope
from smartregression.adapters.storage.schema import index_chunks, knowledge_indexes, repositories
from smartregression.application.index_publication import load_ready_index, publish_index
from smartregression.application.index_store import (
    IndexBusy,
    IndexConflict,
    IndexCorrupt,
    IndexNotReady,
    IndexStorageError,
    prepare_index_publication,
)


@pytest.fixture
def index_case(migrated, index_inputs, tmp_path):
    owner, runtime, _ = migrated
    shared = os.environ.get("SMARTREGRESSION_INDEX_TEST_ROOT")
    root = Path(shared) / uuid4().hex[:12] if shared else tmp_path
    root.mkdir(parents=True, exist_ok=True)
    inputs = index_inputs(root, repository_id="ix-" + uuid4().hex)
    with owner.begin() as connection:
        connection.execute(
            repositories.insert().values(
                repository_id=inputs["manifest"].repository_id,
                source_kind="local",
            )
        )
    artifact_root = root / "artifacts"
    artifact_root.mkdir()
    files = IndexArtifactFiles(artifact_root, source_repository=inputs["source"].repository)
    publication = prepare_index_publication(
        inputs["snapshot"], inputs["manifest"], inputs["configuration"], expected_chunks=2
    )
    return inputs, files, PostgresIndexStore(runtime), publication, owner, runtime


def publish(case, **changes):
    inputs, files, store, publication, _, _ = case
    return publish_index(
        inputs["source"],
        **(
            dict(
                authorization=inputs["authorization"],
                manifest=inputs["manifest"],
                configuration=inputs["configuration"],
                expected_chunks=2,
                attempt_id=uuid4().hex,
                store=store,
                artifacts=files,
            )
            | changes
        ),
    )


def load(case, **changes):
    inputs, files, store, publication, _, _ = case
    return load_ready_index(
        inputs["source"],
        **(
            dict(
                authorization=inputs["authorization"],
                key=publication.record.key,
                configuration=inputs["configuration"],
                store=store,
                artifacts=files,
            )
            | changes
        ),
    )


def test_actual_sql_files_roundtrip_restart_retry_no_excluded_bytes(index_case):
    inputs, files, store, publication, owner, runtime = index_case
    assert load(index_case) is None
    result = publish(index_case)
    assert result == load(index_case)
    assert result == publish(index_case)
    assert load(index_case, store=PostgresIndexStore(runtime)) == result
    with owner.connect() as connection:
        row = (
            connection.execute(sa.select(knowledge_indexes).where(*scope(publication.record.key)))
            .mappings()
            .one()
        )
        assert row["embedding_model"] is None and row["state"] == "ready"
        assert "synthetic_excluded_marker" not in json.dumps(row["record"])
        assert "contents" not in row["record"]
        assert (
            connection.scalar(
                sa.select(sa.func.count())
                .select_from(index_chunks)
                .where(
                    index_chunks.c.repository_id == publication.record.key.repository_id,
                )
            )
            == 2
        )
    assert b"synthetic_excluded_marker" not in files.read(publication.record)
    (inputs["source"].repository / "src/calc.py").write_bytes(b"uncommitted")
    assert load(index_case) == result


@pytest.mark.parametrize("fault", ["missing", "bytes", "metadata", "chunk"])
def test_tampering_fails_verified_ready_load(index_case, fault):
    _, files, _, publication, owner, _ = index_case
    publish(index_case)
    key = publication.record.key
    if fault == "missing":
        (files.root / publication.record.storage_key).unlink()
    elif fault == "bytes":
        (files.root / publication.record.storage_key).write_bytes(b"tampered")
    elif fault == "metadata":
        with owner.begin() as connection:
            record = connection.execute(
                sa.select(knowledge_indexes.c.record).where(*scope(key))
            ).scalar_one()
            record["artifact_sha256"] = "0" * 64
            connection.execute(knowledge_indexes.update().where(*scope(key)).values(record=record))
    else:
        with owner.begin() as connection:
            connection.execute(
                index_chunks.update()
                .where(
                    index_chunks.c.repository_id == key.repository_id,
                )
                .values(content_sha256="0" * 64)
            )
    with pytest.raises(IndexCorrupt):
        load(index_case)


def test_lost_commit_ack_reconciles_by_verified_load_without_delete(index_case):
    _, files, actual_store, publication, _, _ = index_case

    class LostAck:
        def begin(self, *a):
            return actual_store.begin(*a)

        def finish(self, *a, **kw):
            actual_store.finish(*a, **kw)
            raise IndexStorageError()

    with pytest.raises(IndexStorageError):
        publish(index_case, store=LostAck())
    assert (files.root / publication.record.storage_key).exists()
    assert actual_store.load(publication.record.key).state == "ready"
    assert load(index_case) is not None


def test_sql_failure_after_publish_stays_building_and_retries_same_attempt(index_case):
    _, files, store, publication, _, _ = index_case
    attempt = uuid4().hex

    class FailedCommit:
        def begin(self, *a):
            return store.begin(*a)

        def finish(self, *a, **kw):
            raise IndexStorageError()

    with pytest.raises(IndexStorageError):
        publish(index_case, store=FailedCommit(), attempt_id=attempt)
    assert (files.root / publication.record.storage_key).exists()
    with pytest.raises(IndexNotReady):
        load(index_case)
    assert publish(index_case, attempt_id=attempt) == load(index_case)


def test_competing_builds_and_wrong_attempt_cannot_finish(index_case):
    _, _, store, publication, _, _ = index_case
    barrier = Barrier(2)

    def begin():
        attempt = uuid4().hex
        barrier.wait(timeout=10)
        try:
            store.begin(publication.record, attempt)
            return attempt
        except IndexBusy:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [f.result(timeout=25) for f in [pool.submit(begin), pool.submit(begin)]]
    assert results.count(None) == 1
    with pytest.raises(IndexConflict):
        store.finish(publication.record, uuid4().hex)
    winner = next(r for r in results if r is not None)
    publish(index_case, attempt_id=winner)
    assert load(index_case) is not None


def test_failed_publication_restarts_only_with_verified_same_record(index_case, monkeypatch):
    _, files, store, publication, _, _ = index_case
    original = files.publish
    monkeypatch.setattr(files, "publish", lambda *_: (_ for _ in ()).throw(IndexStorageError()))
    with pytest.raises(IndexStorageError):
        publish(index_case)
    assert store.load(publication.record.key).state == "failed"
    monkeypatch.setattr(files, "publish", original)
    assert publish(index_case) == load(index_case)


def test_transaction_rollback_leaves_no_header_chunks_or_snapshot(index_case):
    _, _, store, publication, _, runtime = index_case
    with pytest.raises(RuntimeError, match="rollback"), runtime.begin() as connection:
        BoundIndexStore(connection).begin(publication.record, uuid4().hex)
        raise RuntimeError("rollback")
    assert store.load(publication.record.key) is None
    with runtime.connect() as connection:
        assert (
            connection.scalar(
                sa.select(sa.func.count())
                .select_from(index_chunks)
                .where(
                    index_chunks.c.repository_id == publication.record.key.repository_id,
                )
            )
            == 0
        )


@pytest.mark.parametrize(
    "change",
    [
        {"embedding_model": "fake"},
        {"state": "ready", "error_code": "wrong"},
        {"state": "failed", "error_code": None},
        {"backend": "vector"},
    ],
)
def test_database_rejects_invalid_state_and_fake_model(index_case, change):
    _, _, store, publication, owner, _ = index_case
    store.begin(publication.record, uuid4().hex)
    with pytest.raises(IntegrityError), owner.begin() as connection:
        connection.execute(
            knowledge_indexes.update().where(*scope(publication.record.key)).values(**change)
        )


def test_stale_configuration_never_reuses_ready_index(index_case):
    inputs, _, _, publication, _, _ = index_case
    publish(index_case)
    config = replace(inputs["configuration"], query_version="fixture-query/2")
    assert (
        load(
            index_case,
            key=replace(publication.record.key, configuration_sha256=config.digest),
            configuration=config,
        )
        is None
    )


def test_same_attempt_concurrent_publication_is_idempotent(index_case):
    attempt = uuid4().hex
    barrier = Barrier(2)

    def publish_once():
        barrier.wait(timeout=10)
        return publish(index_case, attempt_id=attempt)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [
            f.result(timeout=25) for f in [pool.submit(publish_once), pool.submit(publish_once)]
        ]
    assert results[0] == results[1] == load(index_case)


def test_runtime_cannot_rewrite_index_payload_or_delete(index_case):
    from sqlalchemy.exc import DBAPIError

    _, _, store, publication, _, runtime = index_case
    store.begin(publication.record, uuid4().hex)
    with pytest.raises(DBAPIError), runtime.begin() as connection:
        connection.execute(
            knowledge_indexes.update()
            .where(*scope(publication.record.key))
            .values(
                record={},
            )
        )
    with pytest.raises(DBAPIError), runtime.begin() as connection:
        connection.execute(knowledge_indexes.delete().where(*scope(publication.record.key)))


def test_conflicting_metadata_for_same_key_is_rejected(index_case):
    _, _, store, publication, _, _ = index_case
    store.begin(publication.record, uuid4().hex)
    with pytest.raises(IndexConflict):
        store.begin(replace(publication.record, artifact_sha256="0" * 64), uuid4().hex)


def test_foreign_repository_is_not_provisioned_implicitly(index_case):
    from smartregression.core.git.snapshots import freeze_snapshot
    from smartregression.core.retrieval.index_manifest import build_index_manifest

    inputs, _, store, _, _, _ = index_case
    snap = freeze_snapshot("unprovisioned-" + uuid4().hex, "a" * 40, (), ())
    manifest = build_index_manifest(
        snap, [], index_version="fixture-index/1", configuration_id=inputs["configuration"].digest
    )
    publication = prepare_index_publication(
        snap, manifest, inputs["configuration"], expected_chunks=0
    )
    with pytest.raises(IndexStorageError):
        store.begin(publication.record, uuid4().hex)

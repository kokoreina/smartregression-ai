"""Actual Git/acquisition and artifact files; metadata port is an explicit double."""

import base64
import json
from dataclasses import replace
from uuid import uuid4

import pytest

from smartregression.adapters.storage.index_artifacts import IndexArtifactFiles
from smartregression.application.index_publication import load_ready_index, publish_index
from smartregression.application.index_store import (
    IndexConfiguration,
    IndexNotReady,
    IndexStorageError,
    StoredIndex,
    decode_index_record,
    prepare_index_publication,
    record_value,
)
from smartregression.core.retrieval.index_manifest import ChunkInput, build_index_manifest


class MemoryStore:
    def __init__(self):
        self.saved = None
        self.fail_commit = False

    def begin(self, record, attempt_id):
        if self.saved is None or self.saved.state == "failed":
            self.saved = StoredIndex(record, "building", attempt_id)
        return self.saved

    def finish(self, record, attempt_id, error_code=None):
        if self.fail_commit:
            raise IndexStorageError()
        self.saved = StoredIndex(
            record, "failed" if error_code else "ready", attempt_id, error_code
        )

    def load(self, key):
        return self.saved


@pytest.fixture
def publication(index_inputs, tmp_path):
    inputs = index_inputs(tmp_path)
    root = tmp_path / "artifacts"
    root.mkdir()
    files = IndexArtifactFiles(root, source_repository=inputs["source"].repository)
    return inputs, files, MemoryStore()


def publish(inputs, files, store, **changes):
    kwargs = {k: inputs[k] for k in ("authorization", "manifest", "configuration")}
    return publish_index(
        inputs["source"],
        **(
            kwargs
            | dict(
                expected_chunks=len(inputs["manifest"].chunks),
                attempt_id=uuid4().hex,
                store=store,
                artifacts=files,
            )
            | changes
        ),
    )


def load(inputs, files, store, **changes):
    record = store.saved.record
    return load_ready_index(
        inputs["source"],
        **(
            dict(
                authorization=inputs["authorization"],
                key=record.key,
                configuration=inputs["configuration"],
                store=store,
                artifacts=files,
            )
            | changes
        ),
    )


def test_publish_retry_restart_and_verified_load_ignore_dirty_source(publication):
    inputs, files, store = publication
    (inputs["source"].repository / "src/calc.py").write_bytes(b"dirty bytes never used")
    first = publish(inputs, files, store)
    assert first == publish(inputs, files, store)
    assert load(inputs, files, store) == first
    assert b"synthetic_excluded_marker" not in first.publication.raw
    assert b".env" not in first.publication.raw
    decoded = json.loads(first.publication.raw)
    assert {c["path"] for c in decoded["manifest"]["chunks"]} == {"src/calc.py", "docs/usage.md"}
    assert all(b"synthetic_excluded_marker" not in base64.b64decode(c) for c in decoded["contents"])
    assert decode_index_record(record_value(first.publication.record)) == first.publication.record


@pytest.mark.parametrize("state", ["building", "failed"])
def test_incomplete_metadata_cannot_load_as_ready(publication, state):
    inputs, files, store = publication
    publish(inputs, files, store)
    store.saved = replace(store.saved, state=state)
    with pytest.raises(IndexNotReady):
        load(inputs, files, store)


@pytest.mark.parametrize("fault", ["bytes", "missing", "record", "wrong_commit", "wrong_config"])
def test_ready_load_revalidates_metadata_artifact_and_source(publication, fault):
    inputs, files, store = publication
    result = publish(inputs, files, store)
    record = result.publication.record
    if fault == "bytes":
        (files.root / record.storage_key).write_bytes(b"tampered")
    elif fault == "missing":
        (files.root / record.storage_key).unlink()
    elif fault == "record":
        store.saved = replace(store.saved, record=replace(record, artifact_sha256="0" * 64))
    elif fault == "wrong_commit":
        pass
    else:
        inputs["configuration"] = replace(inputs["configuration"], query_version="other/2")
    with pytest.raises((IndexStorageError, ValueError)):
        if fault == "wrong_commit":
            load(inputs, files, store, key=replace(record.key, commit="0" * 40))
        else:
            load(inputs, files, store)


def test_db_failure_after_file_publication_retains_orphan_and_building(publication):
    inputs, files, store = publication
    store.fail_commit = True
    with pytest.raises(IndexStorageError):
        publish(inputs, files, store)
    assert store.saved.state == "building"
    assert (files.root / store.saved.record.storage_key).exists()
    with pytest.raises(IndexNotReady):
        load(inputs, files, store)


def test_publication_failure_is_failed_not_ready(publication, monkeypatch):
    inputs, files, store = publication
    monkeypatch.setattr(files, "publish", lambda *_: (_ for _ in ()).throw(IndexStorageError()))
    with pytest.raises(IndexStorageError):
        publish(inputs, files, store)
    assert store.saved.state == "failed"
    assert store.saved.error_code == "artifact_publication_failed"
    assert list(files.root.iterdir()) == []


@pytest.mark.parametrize("fault", ["excluded", "missing_file", "gap", "count", "size", "lines"])
def test_rejected_before_metadata_or_artifact_publication(publication, fault):
    inputs, files, store = publication
    snap, config = inputs["snapshot"], inputs["configuration"]
    chunks = []
    for entry, content in zip(snap.manifest.files, snap.contents, strict=True):
        if fault == "excluded" and entry.path == ".env":
            chunks.append(ChunkInput(entry.path, 1, 1, content))
        if entry.path == "src/calc.py":
            chunks.append(
                ChunkInput(
                    entry.path,
                    2 if fault == "gap" else 1,
                    2,
                    b"# owned fixture\r\n" if fault == "gap" else content,
                )
            )
        if entry.path == "docs/usage.md" and fault != "missing_file":
            chunks.append(ChunkInput(entry.path, 1, 2, content))
    if fault == "size":
        config = replace(config, chunk_bytes=10)
    if fault == "lines":
        config = replace(config, chunk_lines=1)
    manifest = build_index_manifest(
        snap, chunks, index_version="fixture-index/1", configuration_id=config.digest
    )
    with pytest.raises(ValueError):
        publish(
            inputs,
            files,
            store,
            manifest=manifest,
            configuration=config,
            expected_chunks=999 if fault == "count" else len(chunks),
        )
    assert store.saved is None
    assert list(files.root.iterdir()) == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("embedding_model", "fake-model"),
        ("exclusions_version", "disabled"),
        ("chunk_lines", 129),
        ("index_chunks", 10001),
        ("index_bytes", 33554433),
        ("query_seconds", 6),
        ("build_seconds", True),
    ],
)
def test_configuration_bounds_are_versioned(field, value):
    config = IndexConfiguration("p/1", "c/1", "t/1", "q/1", "s/1", "r/1")
    with pytest.raises(ValueError, match="invalid_index_configuration"):
        replace(config, **{field: value}).canonical_bytes()


def test_explicit_empty_eligible_scope_can_publish(index_inputs, tmp_path):
    inputs = index_inputs(tmp_path, contents={".env": b"excluded_fixture=1\n"})
    publication = prepare_index_publication(
        inputs["snapshot"],
        inputs["manifest"],
        inputs["configuration"],
        expected_chunks=0,
    )
    assert publication.record.chunk_sizes == ()
    assert b"excluded_fixture" not in publication.raw


@pytest.mark.parametrize(
    "content",
    [
        b'value = 1\napi_key = "synthetic-fixture-only"\n',
        b"value = 1\n# reference_outcomes: synthetic-fixture-only\n",
    ],
)
def test_partial_chunk_does_not_bypass_full_file_secret_or_label_check(
    index_inputs, tmp_path, content
):
    inputs = index_inputs(tmp_path, contents={"src/config.py": content})
    manifest = build_index_manifest(
        inputs["snapshot"],
        [ChunkInput("src/config.py", 1, 1, b"value = 1\n")],
        index_version="fixture-index/1",
        configuration_id=inputs["configuration"].digest,
    )
    with pytest.raises(ValueError, match="index_source_excluded"):
        prepare_index_publication(
            inputs["snapshot"], manifest, inputs["configuration"], expected_chunks=1
        )


def test_wrong_authorization_rejected_before_metadata_or_file_write(publication, tmp_path):
    from smartregression.application.snapshots import RepositoryAuthorization

    inputs, files, store = publication
    with pytest.raises(ValueError, match="unauthorized_repository"):
        publish(inputs, files, store, authorization=RepositoryAuthorization("foreign", tmp_path))
    assert store.saved is None and list(files.root.iterdir()) == []


def test_build_budget_failure_does_not_create_ready(publication, monkeypatch):
    import smartregression.application.index_publication as boundary

    inputs, files, store = publication
    ticks = iter([0, 61])
    monkeypatch.setattr(boundary.time, "monotonic", lambda: next(ticks))
    with pytest.raises(ValueError, match="index_build_timeout"):
        publish(inputs, files, store)
    assert store.saved is None and list(files.root.iterdir()) == []

"""Real byte publication and trusted acquisition; metadata port is a declared double."""

from dataclasses import replace

import pytest
from test_analysis_workflow import BASE, Source

from smartregression.adapters.storage.index_artifacts import IndexArtifactFiles
from smartregression.application.index_sources import acquire_index_snapshot
from smartregression.application.index_store import IndexNotReady, IndexStorageError, StoredIndex
from smartregression.application.retrieval import PublishedLexicalIndex, lexical_configuration
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.core.retrieval.lexical import search_lexical


class MemoryStore:
    def __init__(self):
        self.saved = None
        self.fail_commit = False

    def begin(self, record, attempt_id):
        if self.saved is None:
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
def publication(tmp_path):
    source = Source(tmp_path)
    authorization = RepositoryAuthorization("fixture", tmp_path)
    snapshot = acquire_index_snapshot(
        source, authorization=authorization, repository_id="fixture", commit=BASE
    )
    root = tmp_path.parent / (tmp_path.name + "-artifacts")
    root.mkdir()
    artifacts = IndexArtifactFiles(root, source_repository=tmp_path)
    store = MemoryStore()
    index = PublishedLexicalIndex(
        source, authorization=authorization, store=store, artifacts=artifacts
    )
    return index, snapshot, artifacts, store


def test_ready_load_reconstructs_lexical_plan_and_verifies_main_artifact(publication):
    index, snapshot, artifacts, store = publication
    config = lexical_configuration()
    assert index.load(snapshot, config) is None
    first = index.ensure(snapshot, config)
    assert index.load(snapshot, config) == first
    restarted = PublishedLexicalIndex(
        index.source, authorization=index.authorization, store=store, artifacts=artifacts
    )
    assert restarted.load(snapshot, config) == first
    assert search_lexical(first, snapshot, terms=("return",)).data.items
    (artifacts.root / store.saved.record.storage_key).write_bytes(b"tampered")
    with pytest.raises(IndexStorageError):
        restarted.load(snapshot, config)


def test_lost_commit_and_building_state_do_not_become_queryable(publication):
    index, snapshot, _, store = publication
    store.fail_commit = True
    with pytest.raises(IndexStorageError):
        index.ensure(snapshot, lexical_configuration())
    assert store.saved.state == "building"
    with pytest.raises(IndexNotReady):
        index.load(snapshot, lexical_configuration())


def test_forged_snapshot_cannot_replace_authorized_acquisition(publication):
    from test_lexical_index import snapshot as freeze

    index, _, _, _ = publication
    forged = freeze({"a.py": b"unrelated = True\n"})
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        index.ensure(forged, lexical_configuration())


def test_configuration_change_does_not_reuse_the_ready_index(publication):
    index, snapshot, _, _ = publication
    config = lexical_configuration()
    index.ensure(snapshot, config)
    from smartregression.application.index_store import IndexConflict

    with pytest.raises(IndexConflict):
        index.load(snapshot, replace(config, chunk_lines=1))

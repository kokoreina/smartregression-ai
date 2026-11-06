"""Authorized acquisition -> verified artifact -> transactional ready metadata.

No source executes. Source/config verification is repeated when loading ready
metadata; hashes or a persisted state label alone never authorize reuse.
"""

import time
from dataclasses import dataclass, field

from smartregression.application.index_sources import acquire_index_snapshot
from smartregression.application.index_store import (
    IndexArtifacts,
    IndexConfiguration,
    IndexConflict,
    IndexCorrupt,
    IndexKey,
    IndexNotReady,
    IndexPublication,
    IndexStore,
    prepare_index_publication,
    validate_attempt,
)
from smartregression.application.snapshots import RepositoryAuthorization, SnapshotSource
from smartregression.core.git.snapshots import SnapshotLimits
from smartregression.core.retrieval.index_manifest import IndexManifest


@dataclass(frozen=True)
class VerifiedIndex:
    publication: IndexPublication
    source_scope: str = field(default="complete_eligible_files", init=False)


def publish_index(
    source: SnapshotSource,
    *,
    authorization: RepositoryAuthorization,
    manifest: IndexManifest,
    configuration: IndexConfiguration,
    expected_chunks: int,
    attempt_id: str,
    store: IndexStore,
    artifacts: IndexArtifacts,
    limits: SnapshotLimits | None = None,
) -> VerifiedIndex:
    validate_attempt(attempt_id)
    started = time.monotonic()
    snapshot = acquire_index_snapshot(
        source,
        authorization=authorization,
        repository_id=manifest.repository_id,
        commit=manifest.commit,
        limits=limits,
    )
    publication = prepare_index_publication(
        snapshot,
        manifest,
        configuration,
        expected_chunks=expected_chunks,
    )
    if time.monotonic() - started > configuration.build_seconds:
        raise ValueError("index_build_timeout")
    previous = store.begin(publication.record, attempt_id)
    if previous.record != publication.record:
        raise IndexConflict()
    if previous.state not in {"building", "ready"}:
        raise IndexCorrupt()
    if previous.state == "ready":
        if artifacts.read(previous.record) != publication.raw:
            raise IndexCorrupt()
        return VerifiedIndex(publication)
    try:
        artifacts.publish(publication)
        if time.monotonic() - started > configuration.build_seconds:
            raise ValueError("index_build_timeout")
    except Exception:
        # Publication has not entered the ready SQL transaction. Retain partial files.
        # If this status write also fails the attempt stays building, never ready.
        store.finish(publication.record, attempt_id, error_code="artifact_publication_failed")
        raise
    # A lost commit acknowledgement is intentionally not retried or marked failed.
    store.finish(publication.record, attempt_id)
    return VerifiedIndex(publication)


def load_ready_index(
    source: SnapshotSource,
    *,
    authorization: RepositoryAuthorization,
    key: IndexKey,
    configuration: IndexConfiguration,
    store: IndexStore,
    artifacts: IndexArtifacts,
    limits: SnapshotLimits | None = None,
) -> VerifiedIndex | None:
    key.__post_init__()
    if configuration.digest != key.configuration_sha256:
        raise IndexConflict()
    # Authorize before disclosing whether metadata exists.
    snapshot = acquire_index_snapshot(
        source,
        authorization=authorization,
        repository_id=key.repository_id,
        commit=key.commit,
        limits=limits,
    )
    if snapshot.manifest.snapshot_id != key.snapshot_id:
        raise IndexConflict()
    stored = store.load(key)
    if stored is None:
        return None
    if stored.state != "ready":
        raise IndexNotReady()
    record = stored.record.validate()
    if record.key != key or record.configuration != configuration:
        raise IndexConflict()
    publication = prepare_index_publication(
        snapshot,
        record.manifest,
        configuration,
        expected_chunks=len(record.manifest.chunks),
    )
    if publication.record != record or artifacts.read(record) != publication.raw:
        raise IndexCorrupt()
    return VerifiedIndex(publication)

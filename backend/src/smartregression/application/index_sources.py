"""Acquire index sources through authorization, never from a serialized trust flag."""

import re

from smartregression.application.snapshots import (
    RepositoryAuthorization,
    SnapshotSource,
    prepare_snapshots,
)
from smartregression.core.git.snapshots import (
    FrozenSnapshot,
    SnapshotLimits,
    validate_frozen_snapshot,
)
from smartregression.core.retrieval.index_manifest import IndexManifest, validate_index_manifest


def acquire_index_snapshot(
    source: SnapshotSource,
    *,
    authorization: RepositoryAuthorization,
    repository_id: str,
    commit: str,
    limits: SnapshotLimits | None = None,
) -> FrozenSnapshot:
    """Read exact frozen Git bytes through an upstream-authorized source adapter.

    Authorization is an operator/service decision; SnapshotSource implementations
    are trusted composition dependencies, not supplied by report/source content.
    Dirty worktree bytes are deliberately irrelevant to a full-commit snapshot.
    This boundary neither publishes artifacts nor marks an index ready.
    """
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ValueError("invalid_commit")
    pair = prepare_snapshots(
        source,
        authorization=authorization,
        repository_id=repository_id,
        base=commit,
        target=commit,
        limits=limits,
    )
    snapshot = pair.target
    validate_frozen_snapshot(snapshot)
    if (
        snapshot.manifest.repository_id != repository_id
        or snapshot.manifest.commit != commit
        or pair.base != snapshot
        or pair.source_repository != str(source.repository.resolve(strict=True))
    ):
        raise ValueError("snapshot_mismatch")
    return snapshot


def verify_index_sources(
    source: SnapshotSource,
    *,
    authorization: RepositoryAuthorization,
    repository_id: str,
    commit: str,
    manifest: IndexManifest,
    index_version: str,
    configuration_id: str,
    limits: SnapshotLimits | None = None,
) -> FrozenSnapshot:
    """Reacquire a persisted manifest's source and verify identity/ranges/hashes.

    Self-consistent caller-generated snapshots are not accepted as acquisition
    evidence. A verified manifest still needs complete publication and committed
    metadata before a consumer may call its index ready.
    """
    snapshot = acquire_index_snapshot(
        source,
        authorization=authorization,
        repository_id=repository_id,
        commit=commit,
        limits=limits,
    )
    validate_index_manifest(
        snapshot, manifest, index_version=index_version, configuration_id=configuration_id
    )
    return snapshot

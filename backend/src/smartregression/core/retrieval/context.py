"""Backend-neutral change-relevant retrieval payload construction."""

from __future__ import annotations

from smartregression.contracts.stages import (
    ImpactPayload,
    RetrievalItem,
    RetrievalPayload,
    RetrievalSource,
    SnapshotIdentity,
)
from smartregression.core.git.snapshots import FrozenSnapshot
from smartregression.core.retrieval.index_manifest import (
    IndexManifest,
    validate_index_manifest,
)


def build_retrieval_payload(
    snapshot: FrozenSnapshot,
    manifest: IndexManifest,
    impact: ImpactPayload,
    *,
    index_version: str,
    configuration_id: str,
) -> RetrievalPayload:
    """Build provenance-only context metadata for an impact candidate set.

    This is a pure, in-memory contract builder. It does not publish or authorize
    a ready index, and it does not return source text or execute retrieved data.
    """

    validate_index_manifest(
        snapshot,
        manifest,
        index_version=index_version,
        configuration_id=configuration_id,
    )
    snapshot_identity = SnapshotIdentity(
        repository_id=snapshot.manifest.repository_id,
        commit=snapshot.manifest.commit,
        snapshot_id=snapshot.manifest.snapshot_id,
    )
    if impact.snapshot.repository_id != snapshot_identity.repository_id:
        raise ValueError("retrieval_repository_mismatch")
    if impact.snapshot.commit != snapshot_identity.commit:
        raise ValueError("retrieval_commit_mismatch")
    if impact.snapshot.snapshot_id != snapshot_identity.snapshot_id:
        raise ValueError("retrieval_snapshot_mismatch")

    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id=manifest.index_id,
        configuration_id=configuration_id,
    )
    candidate_paths = {candidate.path for candidate in impact.candidates}
    items = [
        RetrievalItem(
            snapshot=snapshot_identity,
            index_id=manifest.index_id,
            configuration_id=configuration_id,
            id=chunk.chunk_id,
            path=chunk.path,
            location={
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
            },
            content_sha256=chunk.content_sha256,
            rank=rank,
        )
        for rank, chunk in enumerate(
            (chunk for chunk in manifest.chunks if chunk.path in candidate_paths),
            start=1,
        )
    ]
    return RetrievalPayload(sources=[source], items=items)

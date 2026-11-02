"""Explicit local authorization binding and snapshot-pair preparation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from smartregression.core.git.snapshots import (
    FrozenSnapshot,
    SnapshotLimits,
    SnapshotPair,
    TreeEntry,
    freeze_snapshot,
    validate_snapshot_paths,
)


class SnapshotSource(Protocol):
    repository: Path

    def snapshot_entries(self, sha: str) -> tuple[TreeEntry, ...]: ...

    def read_blob(self, oid: str, *, max_bytes: int) -> bytes: ...


@dataclass(frozen=True)
class RepositoryAuthorization:
    repository_id: str
    local_path: Path


def prepare_snapshots(
    source: SnapshotSource,
    *,
    authorization: RepositoryAuthorization,
    repository_id: str,
    base: str,
    target: str,
    limits: SnapshotLimits | None = None,
) -> SnapshotPair:
    """Use an upstream authorization decision, never infer permission from a hash.

    Only explicit SHA pairs are accepted by the source. PR/ref resolution and
    service access-control decisions remain owned by the integration layer.
    """
    if (
        not repository_id.strip()
        or repository_id != repository_id.strip()
        or repository_id != authorization.repository_id
        or source.repository.resolve(strict=True) != authorization.local_path.resolve(strict=True)
    ):
        raise ValueError("unauthorized_repository")
    limits = limits or SnapshotLimits()

    def prepare(commit: str) -> FrozenSnapshot:
        entries = source.snapshot_entries(commit)
        validate_snapshot_paths([entry.path for entry in entries])
        if (
            len(entries) > limits.max_files
            or any(entry.size < 0 or entry.size > limits.max_file_bytes for entry in entries)
            or sum(entry.size for entry in entries) > limits.max_total_bytes
        ):
            raise ValueError("snapshot_limit")
        contents = tuple(
            source.read_blob(entry.blob_id, max_bytes=limits.max_file_bytes) for entry in entries
        )
        return freeze_snapshot(repository_id, commit, entries, contents)

    frozen_base = prepare(base)
    frozen_target = frozen_base if target == base else prepare(target)
    return SnapshotPair(frozen_base, frozen_target, str(source.repository.resolve(strict=True)))

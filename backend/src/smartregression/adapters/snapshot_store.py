"""Fresh local materialization with a completion marker and trusted-manifest checks."""

import hashlib
import os
import shutil
import stat
from dataclasses import asdict
from pathlib import Path

from smartregression.core.git.snapshots import (
    SnapshotManifest,
    SnapshotPair,
    canonical_json,
    pair_manifest,
    validate_frozen_snapshot,
)


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _reject_links(path: Path) -> None:
    for entry in (path, *path.parents):
        if entry.is_symlink() or entry.is_junction():
            raise ValueError("unsafe_snapshot_destination")


def verify_snapshot(root: Path, *, expected: SnapshotManifest) -> SnapshotManifest:
    """Expected manifest must come from a trusted run, not from the inspected disk."""
    root = _absolute(root)
    _reject_links(root)
    _reject_links(root / "manifest.json")
    _reject_links(root / "files")
    expected_json = canonical_json(asdict(expected))
    manifest_path = root / "manifest.json"
    if (
        manifest_path.stat().st_size != len(expected_json)
        or manifest_path.read_bytes() != expected_json
    ):
        raise ValueError("snapshot_mismatch")
    files = root / "files"
    if not files.is_dir():
        raise ValueError("snapshot_mismatch")
    found = set()
    for path in files.rglob("*"):
        if path.is_symlink() or path.is_junction():
            raise ValueError("snapshot_mismatch")
        if path.is_file():
            found.add(path.relative_to(files).as_posix())
        elif not path.is_dir():
            raise ValueError("snapshot_mismatch")
        if len(found) > len(expected.files):
            raise ValueError("snapshot_mismatch")
    if found != {item.path for item in expected.files}:
        raise ValueError("snapshot_mismatch")
    for item in expected.files:
        path = files / item.path
        if path.stat().st_size != item.size:
            raise ValueError("snapshot_mismatch")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != item.sha256:
            raise ValueError("snapshot_mismatch")
    return expected


def _remove_owned(path: Path) -> None:
    def writable(function, name, error):
        os.chmod(name, stat.S_IWRITE | stat.S_IREAD)
        function(name)

    shutil.rmtree(path, onexc=writable)


def materialize_pair(pair: SnapshotPair, destination: Path, *, source_repository: Path) -> None:
    """Caller controls the workspace. Only fresh owned output is cleaned on failure.

    Read-only file bits deter accidental edits. Hash verification detects later
    mutations; this local store does not isolate against a concurrent host attacker.
    Consumers use pair.json as the completion marker.
    """
    destination = _absolute(destination)
    _reject_links(destination)
    validate_frozen_snapshot(pair.base)
    validate_frozen_snapshot(pair.target)
    if pair.base.manifest.repository_id != pair.target.manifest.repository_id:
        raise ValueError("unauthorized_repository")
    source = source_repository.resolve(strict=True)
    if str(source) != pair.source_repository:
        raise ValueError("unauthorized_repository")
    if destination.is_relative_to(source):
        raise ValueError("snapshot_destination_inside_source")
    if destination.exists():
        raise ValueError("snapshot_destination_exists")
    if not destination.parent.is_dir():
        raise ValueError("snapshot_parent_missing")
    destination.mkdir(mode=0o700, exist_ok=False)
    try:
        for name, snapshot in (("base", pair.base), ("target", pair.target)):
            root = destination / name
            files = root / "files"
            files.mkdir(parents=True)
            for item, content in zip(snapshot.manifest.files, snapshot.contents, strict=True):
                target = files / item.path
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(content)
                target.chmod(stat.S_IREAD)
            with (root / "manifest.json").open("xb") as stream:
                stream.write(canonical_json(asdict(snapshot.manifest)))
            verify_snapshot(root, expected=snapshot.manifest)
        marker = destination / "pair.pending"
        with marker.open("xb") as stream:
            stream.write(canonical_json(pair_manifest(pair)))
        marker.replace(destination / "pair.json")
    except BaseException:
        _remove_owned(destination)
        raise

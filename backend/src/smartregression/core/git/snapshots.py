"""Bounded immutable snapshot values and deterministic content identity."""

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class SnapshotLimits:
    max_files: int = 1000
    max_file_bytes: int = 1_000_000
    max_total_bytes: int = 16_000_000

    def __post_init__(self) -> None:
        values = (self.max_files, self.max_file_bytes, self.max_total_bytes)
        if any(type(v) is not int or v < 1 for v in values) or (
            self.max_files > 10_000
            or self.max_file_bytes > 1_000_000
            or self.max_total_bytes > 64_000_000
        ):
            raise ValueError("invalid_snapshot_limits")


@dataclass(frozen=True)
class TreeEntry:
    path: str
    mode: str
    blob_id: str
    size: int


@dataclass(frozen=True)
class SnapshotFile:
    path: str
    mode: str
    blob_id: str
    size: int
    sha256: str


@dataclass(frozen=True)
class SnapshotManifest:
    repository_id: str
    commit: str
    files: tuple[SnapshotFile, ...]
    snapshot_id: str
    schema_version: str = "snapshot/1"
    materializer_version: str = "git-blobs/1"


@dataclass(frozen=True)
class FrozenSnapshot:
    manifest: SnapshotManifest
    contents: tuple[bytes, ...] = field(repr=False)


@dataclass(frozen=True)
class SnapshotPair:
    base: FrozenSnapshot
    target: FrozenSnapshot
    source_repository: str = field(repr=False)


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n"
    ).encode()


def pair_manifest(pair: SnapshotPair) -> dict:
    return {
        "schema_version": "snapshot-pair/1",
        "comparison_mode": "direct_two_tree",
        "base": asdict(pair.base.manifest),
        "target": asdict(pair.target.manifest),
    }


def validate_snapshot_paths(paths: list[str]) -> None:
    seen = set()
    for path in paths:
        parts = path.split("/")
        if (
            not path
            or any(c in path for c in '\\:<>"|?*')
            or any(ord(c) < 32 or ord(c) == 127 for c in path)
        ):
            raise ValueError("unsafe_snapshot_path")
        for part in parts:
            stem = part.split(".")[0].casefold()
            if (
                part in {"", ".", ".."}
                or part != part.strip()
                or part.endswith(".")
                or part.casefold() == ".git"
                or stem in {"con", "prn", "aux", "nul", "conin$", "conout$"}
                or re.fullmatch(r"(?:com|lpt)[1-9¹²³]", stem)
            ):
                raise ValueError("unsafe_snapshot_path")
        key = unicodedata.normalize("NFC", path).casefold()
        if key in seen:
            raise ValueError("snapshot_path_collision")
        seen.add(key)
    for path in seen:
        parts = path.split("/")
        if any("/".join(parts[:i]) in seen for i in range(1, len(parts))):
            raise ValueError("snapshot_path_collision")


def freeze_snapshot(
    repository_id: str, commit: str, entries: tuple[TreeEntry, ...], contents: tuple[bytes, ...]
) -> FrozenSnapshot:
    if len(entries) != len(contents):
        raise ValueError("snapshot_mismatch")
    validate_snapshot_paths([entry.path for entry in entries])
    if not repository_id.strip() or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
        raise ValueError("snapshot_mismatch")
    files = []
    for entry, content in zip(entries, contents, strict=True):
        if entry.mode not in {"100644", "100755"} or not re.fullmatch(
            r"(?:[0-9a-f]{40}|[0-9a-f]{64})", entry.blob_id
        ):
            raise ValueError("unsupported_snapshot_entry")
        algorithm = "sha1" if len(entry.blob_id) == 40 else "sha256"
        git_hash = hashlib.new(algorithm, b"blob " + str(len(content)).encode() + b"\0" + content)
        if len(content) != entry.size or git_hash.hexdigest() != entry.blob_id:
            raise ValueError("snapshot_mismatch")
        files.append(
            SnapshotFile(
                entry.path,
                entry.mode,
                entry.blob_id,
                len(content),
                hashlib.sha256(content).hexdigest(),
            )
        )
    payload = {
        "schema_version": "snapshot/1",
        "materializer_version": "git-blobs/1",
        "repository_id": repository_id,
        "commit": commit,
        "files": [asdict(f) for f in files],
    }
    identity = hashlib.sha256(canonical_json(payload)).hexdigest()
    return FrozenSnapshot(SnapshotManifest(repository_id, commit, tuple(files), identity), contents)


def validate_frozen_snapshot(snapshot: FrozenSnapshot) -> None:
    manifest = snapshot.manifest
    entries = tuple(TreeEntry(f.path, f.mode, f.blob_id, f.size) for f in manifest.files)
    if (
        freeze_snapshot(manifest.repository_id, manifest.commit, entries, snapshot.contents)
        != snapshot
    ):
        raise ValueError("snapshot_mismatch")

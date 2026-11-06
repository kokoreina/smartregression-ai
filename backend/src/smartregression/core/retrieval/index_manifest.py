"""Deterministic, backend-neutral snapshot index and chunk manifests."""

from __future__ import annotations

import hashlib
import json
import re
from array import array
from dataclasses import dataclass, field
from typing import Literal

from smartregression.core.git.snapshots import (
    FrozenSnapshot,
    validate_frozen_snapshot,
    validate_snapshot_paths,
)

IndexState = Literal["building", "ready", "failed"]
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")


def _validate_version(value: str, code: str) -> None:
    if not isinstance(value, str) or not _VERSION.fullmatch(value):
        raise ValueError(code)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


class _PhysicalLines:
    """Per-operation byte offsets; no global cache across snapshots or sources."""

    def __init__(self, content: bytes) -> None:
        self.content = content
        # Compact offsets avoid retaining Python integers per physical line.
        # Authorized snapshot files are bounded below the uint32 address space.
        self.ends = array("I", (m.end() for m in re.finditer(rb"\r\n|\r|\n", content)))
        if content and (not self.ends or self.ends[-1] != len(content)):
            self.ends.append(len(content))

    def range_bytes(self, line_start: int, line_end: int) -> bytes:
        if line_start < 1 or line_end < line_start or line_end > len(self.ends):
            raise ValueError("invalid_source_range")
        start = 0 if line_start == 1 else self.ends[line_start - 2]
        return self.content[start : self.ends[line_end - 1]]


def _range_bytes(content: bytes, line_start: int, line_end: int) -> bytes:
    return _PhysicalLines(content).range_bytes(line_start, line_end)


def _validate_digest(value: str, code: str) -> None:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ValueError(code)


def _validate_commit(value: str, code: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
        raise ValueError(code)


def _validate_nonempty(value: str, code: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(code)


def _chunk_identity(
    *,
    repository_id: str,
    commit: str,
    snapshot_id: str,
    index_version: str,
    configuration_id: str,
    path: str,
    line_start: int,
    line_end: int,
    content_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": "chunk/1",
        "repository_id": repository_id,
        "commit": commit,
        "snapshot_id": snapshot_id,
        "index_version": index_version,
        "configuration_id": configuration_id,
        "path": path,
        "line_start": line_start,
        "line_end": line_end,
        "content_sha256": content_sha256,
    }


def _chunk_id(chunk: ChunkManifest, *, index_version: str, configuration_id: str) -> str:
    return hashlib.sha256(
        _canonical(
            _chunk_identity(
                repository_id=chunk.repository_id,
                commit=chunk.commit,
                snapshot_id=chunk.snapshot_id,
                index_version=index_version,
                configuration_id=configuration_id,
                path=chunk.path,
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                content_sha256=chunk.content_sha256,
            )
        )
    ).hexdigest()


def _index_identity(manifest: IndexManifest) -> dict[str, object]:
    return {
        "schema_version": manifest.schema_version,
        "repository_id": manifest.repository_id,
        "commit": manifest.commit,
        "snapshot_id": manifest.snapshot_id,
        "index_version": manifest.index_version,
        "configuration_id": manifest.configuration_id,
        "chunks": [chunk.as_dict() for chunk in manifest.chunks],
    }


@dataclass(frozen=True)
class ChunkInput:
    path: str
    line_start: int
    line_end: int
    content: bytes

    def __post_init__(self) -> None:
        try:
            validate_snapshot_paths([self.path])
        except ValueError as exc:
            raise ValueError("invalid_chunk_path") from exc
        if (
            type(self.line_start) is not int
            or type(self.line_end) is not int
            or self.line_start < 1
            or self.line_end < self.line_start
        ):
            raise ValueError("invalid_source_range")
        if not isinstance(self.content, bytes):
            raise ValueError("invalid_chunk_content")


@dataclass(frozen=True)
class ChunkManifest:
    chunk_id: str
    repository_id: str
    commit: str
    snapshot_id: str
    path: str
    line_start: int
    line_end: int
    content_sha256: str

    def __post_init__(self) -> None:
        _validate_digest(self.chunk_id, "invalid_chunk_identity")
        _validate_nonempty(self.repository_id, "invalid_repository_identity")
        _validate_commit(self.commit, "invalid_commit_identity")
        _validate_digest(self.snapshot_id, "invalid_snapshot_identity")
        try:
            validate_snapshot_paths([self.path])
        except ValueError as exc:
            raise ValueError("invalid_chunk_path") from exc
        if (
            type(self.line_start) is not int
            or type(self.line_end) is not int
            or self.line_start < 1
            or self.line_end < self.line_start
        ):
            raise ValueError("invalid_source_range")
        _validate_digest(self.content_sha256, "invalid_content_hash")

    def as_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "repository_id": self.repository_id,
            "commit": self.commit,
            "snapshot_id": self.snapshot_id,
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "content_sha256": self.content_sha256,
        }


@dataclass(frozen=True)
class IndexManifest:
    index_id: str
    repository_id: str
    commit: str
    snapshot_id: str
    index_version: str
    configuration_id: str
    chunks: tuple[ChunkManifest, ...]
    schema_version: str = "index/1"

    def __post_init__(self) -> None:
        if self.schema_version != "index/1":
            raise ValueError("invalid_index_schema")
        _validate_digest(self.index_id, "invalid_index_identity")
        _validate_nonempty(self.repository_id, "invalid_repository_identity")
        _validate_commit(self.commit, "invalid_commit_identity")
        _validate_digest(self.snapshot_id, "invalid_snapshot_identity")
        _validate_version(self.index_version, "invalid_index_version")
        _validate_version(self.configuration_id, "invalid_configuration_id")
        if type(self.chunks) is not tuple:
            raise ValueError("invalid_chunk_manifest")
        if any(not isinstance(chunk, ChunkManifest) for chunk in self.chunks):
            raise ValueError("invalid_chunk_manifest")
        chunk_ids = [chunk.chunk_id for chunk in self.chunks]
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("duplicate_chunk_identity")
        if chunk_ids != sorted(chunk_ids):
            raise ValueError("noncanonical_chunk_order")
        for chunk in self.chunks:
            if (
                chunk.repository_id != self.repository_id
                or chunk.commit != self.commit
                or chunk.snapshot_id != self.snapshot_id
                or _chunk_id(
                    chunk,
                    index_version=self.index_version,
                    configuration_id=self.configuration_id,
                )
                != chunk.chunk_id
            ):
                raise ValueError("inconsistent_chunk_identity")
        expected_id = hashlib.sha256(_canonical(_index_identity(self))).hexdigest()
        if self.index_id != expected_id:
            raise ValueError("inconsistent_index_identity")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "index_id": self.index_id,
            "repository_id": self.repository_id,
            "commit": self.commit,
            "snapshot_id": self.snapshot_id,
            "index_version": self.index_version,
            "configuration_id": self.configuration_id,
            "chunks": [chunk.as_dict() for chunk in self.chunks],
        }


@dataclass(frozen=True, init=False)
class IndexBuild:
    """Run-local lifecycle state; publication is only valid for a ready manifest."""

    state: IndexState
    repository_id: str
    commit: str
    snapshot_id: str
    index_version: str
    configuration_id: str
    expected_chunks: int | None
    chunks: tuple[ChunkInput, ...] = ()
    error_code: str | None = None
    _manifest: IndexManifest | None = field(default=None, repr=False)

    def add_chunk(self, chunk: ChunkInput) -> IndexBuild:
        if self.state != "building":
            raise ValueError("invalid_index_transition")
        return _new_index_build(
            state=self.state,
            repository_id=self.repository_id,
            commit=self.commit,
            snapshot_id=self.snapshot_id,
            index_version=self.index_version,
            configuration_id=self.configuration_id,
            expected_chunks=self.expected_chunks,
            chunks=(*self.chunks, chunk),
            error_code=self.error_code,
            manifest=self._manifest,
        )

    def fail(self, error_code: str) -> IndexBuild:
        if self.state != "building" or not re.fullmatch(r"[a-z][a-z0-9_]*", error_code):
            raise ValueError("invalid_index_transition")
        return _new_index_build(
            state="failed",
            repository_id=self.repository_id,
            commit=self.commit,
            snapshot_id=self.snapshot_id,
            index_version=self.index_version,
            configuration_id=self.configuration_id,
            expected_chunks=self.expected_chunks,
            chunks=self.chunks,
            error_code=error_code,
            manifest=None,
        )

    def ready(self) -> IndexBuild:
        if self.state != "building":
            raise ValueError("invalid_index_transition")
        raise ValueError("trusted_snapshot_acquisition_required")

    @property
    def manifest(self) -> IndexManifest:
        if self.state != "ready" or self._manifest is None:
            raise ValueError("index_not_ready")
        return self._manifest


def start_index_build(
    snapshot: FrozenSnapshot,
    *,
    index_version: str,
    configuration_id: str,
    expected_chunks: int | None = None,
) -> IndexBuild:
    _validate_snapshot_consistency(snapshot)
    validate_index_manifest_input(snapshot, index_version, configuration_id, expected_chunks)
    return _new_index_build(
        state="building",
        repository_id=snapshot.manifest.repository_id,
        commit=snapshot.manifest.commit,
        snapshot_id=snapshot.manifest.snapshot_id,
        index_version=index_version,
        configuration_id=configuration_id,
        expected_chunks=expected_chunks,
        chunks=(),
        error_code=None,
        manifest=None,
    )


def _new_index_build(
    *,
    state: IndexState,
    repository_id: str,
    commit: str,
    snapshot_id: str,
    index_version: str,
    configuration_id: str,
    expected_chunks: int | None,
    chunks: tuple[ChunkInput, ...],
    error_code: str | None,
    manifest: IndexManifest | None,
) -> IndexBuild:
    if state not in {"building", "failed"}:
        raise ValueError("invalid_index_state")
    if manifest is not None:
        raise ValueError("ready_manifest_unavailable")
    if type(chunks) is not tuple:
        raise ValueError("invalid_chunk_manifest")
    if any(not isinstance(chunk, ChunkInput) for chunk in chunks):
        raise ValueError("invalid_chunk_manifest")
    validate_index_build_identity(
        repository_id,
        commit,
        snapshot_id,
        index_version,
        configuration_id,
        expected_chunks,
    )
    if state == "building" and error_code is not None:
        raise ValueError("invalid_index_state")
    if state == "failed" and (
        error_code is None or not re.fullmatch(r"[a-z][a-z0-9_]*", error_code)
    ):
        raise ValueError("invalid_index_state")
    result = object.__new__(IndexBuild)
    for name, value in {
        "state": state,
        "repository_id": repository_id,
        "commit": commit,
        "snapshot_id": snapshot_id,
        "index_version": index_version,
        "configuration_id": configuration_id,
        "expected_chunks": expected_chunks,
        "chunks": chunks,
        "error_code": error_code,
        "_manifest": manifest,
    }.items():
        object.__setattr__(result, name, value)
    return result


def validate_index_build_identity(
    repository_id: str,
    commit: str,
    snapshot_id: str,
    index_version: str,
    configuration_id: str,
    expected_chunks: int | None,
) -> None:
    _validate_nonempty(repository_id, "invalid_repository_identity")
    _validate_commit(commit, "invalid_commit_identity")
    _validate_digest(snapshot_id, "invalid_snapshot_identity")
    _validate_version(index_version, "invalid_index_version")
    _validate_version(configuration_id, "invalid_configuration_id")
    if expected_chunks is not None and (type(expected_chunks) is not int or expected_chunks < 0):
        raise ValueError("invalid_expected_chunk_count")


def _validate_snapshot_consistency(snapshot: FrozenSnapshot) -> None:
    validate_frozen_snapshot(snapshot)


def validate_index_manifest_input(
    snapshot: FrozenSnapshot,
    index_version: str,
    configuration_id: str,
    expected_chunks: int | None,
) -> None:
    if not snapshot.manifest.snapshot_id or not _DIGEST.fullmatch(snapshot.manifest.snapshot_id):
        raise ValueError("invalid_snapshot_identity")
    _validate_version(index_version, "invalid_index_version")
    _validate_version(configuration_id, "invalid_configuration_id")
    if expected_chunks is not None and (type(expected_chunks) is not int or expected_chunks < 0):
        raise ValueError("invalid_expected_chunk_count")


def build_index_manifest(
    snapshot: FrozenSnapshot,
    chunks: tuple[ChunkInput, ...] | list[ChunkInput],
    *,
    index_version: str,
    configuration_id: str,
) -> IndexManifest:
    _validate_snapshot_consistency(snapshot)
    validate_index_manifest_input(snapshot, index_version, configuration_id, None)
    if not isinstance(chunks, (tuple, list)) or any(
        not isinstance(chunk, ChunkInput) for chunk in chunks
    ):
        raise ValueError("invalid_chunk_manifest")
    files = {
        item.path: content
        for item, content in zip(snapshot.manifest.files, snapshot.contents, strict=True)
    }
    records: list[ChunkManifest] = []
    seen: set[str] = set()
    ranges: dict[str, _PhysicalLines] = {}
    for chunk in chunks:
        content = files.get(chunk.path)
        if content is None:
            raise ValueError("unknown_snapshot_path")
        if type(chunk.line_start) is not int or type(chunk.line_end) is not int:
            raise ValueError("invalid_source_range")
        if chunk.path not in ranges:
            ranges[chunk.path] = _PhysicalLines(content)
        expected = ranges[chunk.path].range_bytes(chunk.line_start, chunk.line_end)
        if chunk.content != expected:
            raise ValueError("chunk_content_mismatch")
        digest = _sha256(chunk.content)
        identity = _chunk_identity(
            repository_id=snapshot.manifest.repository_id,
            commit=snapshot.manifest.commit,
            snapshot_id=snapshot.manifest.snapshot_id,
            index_version=index_version,
            configuration_id=configuration_id,
            path=chunk.path,
            line_start=chunk.line_start,
            line_end=chunk.line_end,
            content_sha256=digest,
        )
        chunk_id = hashlib.sha256(_canonical(identity)).hexdigest()
        if chunk_id in seen:
            raise ValueError("duplicate_chunk_identity")
        seen.add(chunk_id)
        records.append(
            ChunkManifest(
                chunk_id,
                snapshot.manifest.repository_id,
                snapshot.manifest.commit,
                snapshot.manifest.snapshot_id,
                chunk.path,
                chunk.line_start,
                chunk.line_end,
                digest,
            )
        )
    records.sort(key=lambda item: item.chunk_id)
    manifest = _new_index_manifest(
        repository_id=snapshot.manifest.repository_id,
        commit=snapshot.manifest.commit,
        snapshot_id=snapshot.manifest.snapshot_id,
        index_version=index_version,
        configuration_id=configuration_id,
        chunks=tuple(records),
    )
    return manifest


def _new_index_manifest(
    *,
    repository_id: str,
    commit: str,
    snapshot_id: str,
    index_version: str,
    configuration_id: str,
    chunks: tuple[ChunkManifest, ...],
) -> IndexManifest:
    manifest = object.__new__(IndexManifest)
    for name, value in {
        "index_id": "",
        "repository_id": repository_id,
        "commit": commit,
        "snapshot_id": snapshot_id,
        "index_version": index_version,
        "configuration_id": configuration_id,
        "chunks": chunks,
        "schema_version": "index/1",
    }.items():
        object.__setattr__(manifest, name, value)
    object.__setattr__(
        manifest, "index_id", hashlib.sha256(_canonical(_index_identity(manifest))).hexdigest()
    )
    IndexManifest.__post_init__(manifest)
    return manifest


def canonical_manifest_bytes(manifest: IndexManifest) -> bytes:
    _validate_index_manifest_object(manifest)
    return _canonical(manifest.as_dict())


def _validate_index_manifest_object(manifest: IndexManifest) -> None:
    if not isinstance(manifest, IndexManifest):
        raise ValueError("invalid_index_manifest")
    IndexManifest.__post_init__(manifest)


def validate_index_manifest(
    snapshot: FrozenSnapshot,
    manifest: IndexManifest,
    *,
    index_version: str,
    configuration_id: str,
) -> None:
    _validate_snapshot_consistency(snapshot)
    _validate_index_manifest_object(manifest)
    if (
        manifest.repository_id != snapshot.manifest.repository_id
        or manifest.commit != snapshot.manifest.commit
        or manifest.snapshot_id != snapshot.manifest.snapshot_id
        or manifest.index_version != index_version
        or manifest.configuration_id != configuration_id
    ):
        raise ValueError("stale_index")
    files = {
        item.path: content
        for item, content in zip(snapshot.manifest.files, snapshot.contents, strict=True)
    }
    if any(chunk.path not in files for chunk in manifest.chunks):
        raise ValueError("unknown_snapshot_path")
    ranges = {path: _PhysicalLines(files[path]) for path in {c.path for c in manifest.chunks}}
    expected = build_index_manifest(
        snapshot,
        tuple(
            ChunkInput(
                chunk.path,
                chunk.line_start,
                chunk.line_end,
                ranges[chunk.path].range_bytes(chunk.line_start, chunk.line_end),
            )
            for chunk in manifest.chunks
        ),
        index_version=index_version,
        configuration_id=configuration_id,
    )
    if expected != manifest:
        raise ValueError("index_manifest_mismatch")

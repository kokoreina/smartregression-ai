"""Internal index metadata/artifact contracts; no SQL, filesystem or ready bypass."""

import base64
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Literal, Protocol

from smartregression.core.git.snapshots import FrozenSnapshot, canonical_json
from smartregression.core.retrieval.exclusions import EXCLUSIONS_VERSION, exclusion_reason
from smartregression.core.retrieval.index_manifest import (
    ChunkManifest,
    IndexManifest,
    canonical_manifest_bytes,
    validate_index_manifest,
)
from smartregression.core.retrieval.ranked_context import extract_range_bytes

MAX_INDEX_ARTIFACT_BYTES = 48 * 1024 * 1024


class IndexStorageError(RuntimeError):
    code = "index_storage_failed"

    def __init__(self):
        super().__init__(self.code)


class IndexConflict(IndexStorageError):
    code = "index_storage_conflict"


class IndexBusy(IndexStorageError):
    code = "index_build_in_progress"


class IndexNotReady(IndexStorageError):
    code = "index_not_ready"


class IndexCorrupt(IndexStorageError):
    code = "index_artifact_corrupt"


@dataclass(frozen=True)
class IndexConfiguration:
    parser_version: str
    chunker_version: str
    tokenizer_version: str
    query_version: str
    scoring_version: str
    ranking_version: str
    exclusions_version: str = EXCLUSIONS_VERSION
    backend: str = "local-lexical"
    embedding_model: None = None
    chunk_lines: int = 128
    chunk_bytes: int = 8192
    index_chunks: int = 10_000
    index_bytes: int = 32 * 1024 * 1024
    query_terms: int = 64
    context_chunks: int = 20
    context_bytes: int = 65536
    build_seconds: int = 60
    query_seconds: int = 5

    def canonical_bytes(self) -> bytes:
        if (
            any(
                not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", v)
                for v in (
                    self.parser_version,
                    self.chunker_version,
                    self.tokenizer_version,
                    self.query_version,
                    self.scoring_version,
                    self.ranking_version,
                )
            )
            or self.exclusions_version != EXCLUSIONS_VERSION
            or self.backend != "local-lexical"
            or self.embedding_model is not None
            or any(
                type(v) is not int or not 0 < v <= cap
                for v, cap in (
                    (self.chunk_lines, 128),
                    (self.chunk_bytes, 8192),
                    (self.index_chunks, 10_000),
                    (self.index_bytes, 32 * 1024 * 1024),
                    (self.query_terms, 64),
                    (self.context_chunks, 20),
                    (self.context_bytes, 65536),
                    (self.build_seconds, 60),
                    (self.query_seconds, 5),
                )
            )
        ):
            raise ValueError("invalid_index_configuration")
        return canonical_json(asdict(self))

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


@dataclass(frozen=True)
class IndexKey:
    repository_id: str
    commit: str
    snapshot_id: str
    index_version: str
    configuration_sha256: str

    def __post_init__(self):
        if (
            not isinstance(self.repository_id, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", self.repository_id)
            or not isinstance(self.commit, str)
            or not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", self.commit)
            or any(
                not isinstance(v, str) or not re.fullmatch(r"[a-f0-9]{64}", v)
                for v in (self.snapshot_id, self.configuration_sha256)
            )
            or not isinstance(self.index_version, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", self.index_version)
        ):
            raise ValueError("invalid_index_key")


@dataclass(frozen=True)
class IndexRecord:
    manifest: IndexManifest
    configuration: IndexConfiguration
    artifact_sha256: str
    artifact_size: int
    chunk_sizes: tuple[int, ...]
    snapshot_version: str = "snapshot/1"
    materializer_version: str = "git-blobs/1"

    @property
    def key(self) -> IndexKey:
        m = self.manifest
        return IndexKey(
            m.repository_id, m.commit, m.snapshot_id, m.index_version, self.configuration.digest
        )

    @property
    def storage_key(self) -> str:
        return "indexes/" + self.artifact_sha256 + ".json"

    def validate(self) -> IndexRecord:
        canonical_manifest_bytes(self.manifest)
        self.key.__post_init__()
        if (
            self.manifest.configuration_id != self.configuration.digest
            or not re.fullmatch(r"[a-f0-9]{64}", self.artifact_sha256)
            or type(self.artifact_size) is not int
            or not 0 < self.artifact_size <= MAX_INDEX_ARTIFACT_BYTES
            or type(self.chunk_sizes) is not tuple
            or len(self.chunk_sizes) != len(self.manifest.chunks)
            or len(self.chunk_sizes) > self.configuration.index_chunks
            or sum(self.chunk_sizes) > self.configuration.index_bytes
            or any(
                type(n) is not int or not 0 < n <= self.configuration.chunk_bytes
                for n in self.chunk_sizes
            )
            or any(
                c.line_end - c.line_start + 1 > self.configuration.chunk_lines
                for c in self.manifest.chunks
            )
            or self.snapshot_version != "snapshot/1"
            or self.materializer_version != "git-blobs/1"
        ):
            raise ValueError("invalid_index_record")
        return self


@dataclass(frozen=True)
class IndexPublication:
    record: IndexRecord
    raw: bytes = field(repr=False)


@dataclass(frozen=True)
class StoredIndex:
    record: IndexRecord
    state: Literal["building", "ready", "failed"]
    attempt_id: str
    error_code: str | None = None


def validate_attempt(attempt_id: str) -> None:
    if not isinstance(attempt_id, str) or not re.fullmatch(r"[a-f0-9]{32}", attempt_id):
        raise ValueError("invalid_index_attempt")


def prepare_index_publication(
    snapshot: FrozenSnapshot,
    manifest: IndexManifest,
    configuration: IndexConfiguration,
    *,
    expected_chunks: int,
) -> IndexPublication:
    """Pure validation; the application publisher must independently acquire source.

    Validate the producer count and physical coverage of every eligible nonempty
    file. This does not create chunks, judge semantic recall, or authenticate callers.
    """
    validate_index_manifest(
        snapshot,
        manifest,
        index_version=manifest.index_version,
        configuration_id=configuration.digest,
    )
    if type(expected_chunks) is not int or expected_chunks != len(manifest.chunks):
        raise ValueError("incomplete_index_build")
    files = {f.path: raw for f, raw in zip(snapshot.manifest.files, snapshot.contents, strict=True)}
    denied = {p for p, raw in files.items() if exclusion_reason(p, raw) is not None}
    if any(c.path in denied for c in manifest.chunks):
        raise ValueError("index_source_excluded")
    for path, content in files.items():
        if path in denied or not content:
            continue
        count = len(re.findall(rb"\r\n|\r|\n", content)) + int(not content.endswith((b"\r", b"\n")))
        cursor = 1
        for start, end in sorted(
            (c.line_start, c.line_end) for c in manifest.chunks if c.path == path
        ):
            if start > cursor:
                raise ValueError("incomplete_index_build")
            cursor = max(cursor, end + 1)
        if cursor != count + 1:
            raise ValueError("incomplete_index_build")
    chunks = tuple(
        extract_range_bytes(files[c.path], c.line_start, c.line_end) for c in manifest.chunks
    )
    raw = canonical_json(
        {
            "format": "index-artifact/1",
            "manifest": manifest.as_dict(),
            "configuration": json.loads(configuration.canonical_bytes()),
            "contents": [base64.b64encode(b).decode("ascii") for b in chunks],
        }
    )
    record = IndexRecord(
        manifest,
        configuration,
        hashlib.sha256(raw).hexdigest(),
        len(raw),
        tuple(len(b) for b in chunks),
    ).validate()
    return IndexPublication(record, raw)


def decode_index_record(value: dict) -> IndexRecord:
    """Reconstruct metadata from SQL; validate exact fields and deterministic identity."""
    try:
        if type(value) is not dict or set(value) != {
            "manifest",
            "configuration",
            "artifact_sha256",
            "artifact_size",
            "chunk_sizes",
            "snapshot_version",
            "materializer_version",
        }:
            raise IndexCorrupt()
        m = dict(value["manifest"])
        m["chunks"] = tuple(ChunkManifest(**c) for c in m["chunks"])
        return IndexRecord(
            IndexManifest(**m),
            IndexConfiguration(**value["configuration"]),
            value["artifact_sha256"],
            value["artifact_size"],
            tuple(value["chunk_sizes"]),
            value["snapshot_version"],
            value["materializer_version"],
        ).validate()
    except ValueError, TypeError, KeyError, AttributeError:
        raise IndexCorrupt() from None


def record_value(record: IndexRecord) -> dict:
    record.validate()
    return {
        "manifest": record.manifest.as_dict(),
        "configuration": json.loads(record.configuration.canonical_bytes()),
        "artifact_sha256": record.artifact_sha256,
        "artifact_size": record.artifact_size,
        "chunk_sizes": list(record.chunk_sizes),
        "snapshot_version": record.snapshot_version,
        "materializer_version": record.materializer_version,
    }


class IndexStore(Protocol):
    def begin(self, record: IndexRecord, attempt_id: str) -> StoredIndex: ...
    def finish(
        self, record: IndexRecord, attempt_id: str, error_code: str | None = None
    ) -> None: ...
    def load(self, key: IndexKey) -> StoredIndex | None: ...


class IndexArtifacts(Protocol):
    def publish(self, publication: IndexPublication) -> None: ...
    def read(self, record: IndexRecord) -> bytes: ...

"""Bounded local AST/lexical retrieval; source is data and never executed."""

import re
from dataclasses import dataclass
from time import monotonic
from typing import Protocol

from smartregression.contracts.stages import (
    ChangePayload,
    ImpactPayload,
    RetrievalItem,
    RetrievalPayload,
    RetrievalSource,
    SnapshotIdentity,
    StageIssue,
    StageResult,
)
from smartregression.core.git.snapshots import (
    FrozenSnapshot,
    validate_frozen_snapshot,
)
from smartregression.core.impact.python_snapshot import inspect_python
from smartregression.core.retrieval.exclusions import exclusion_reason
from smartregression.core.retrieval.index_manifest import (
    ChunkInput,
    IndexManifest,
    build_index_manifest,
    validate_index_manifest,
)
from smartregression.core.retrieval.ranked_context import rank_and_validate_context

INDEX_VERSION = "lexical-ast/1"
PARSER_VERSION = "python-ast/3.14"
CHUNKER_VERSION = "ast-physical/1"
TOKENIZER_VERSION = "distinct-terms/1"
QUERY_VERSION = "change-identifiers/1"
SCORING_VERSION = "distinct-weighted/1"
RANKING_VERSION = "2.12-v1"


class LexicalConfiguration(Protocol):
    """Validated immutable configuration supplied by trusted application code."""

    chunk_lines: int
    chunk_bytes: int
    index_chunks: int
    index_bytes: int
    query_terms: int
    context_chunks: int
    context_bytes: int
    build_seconds: int
    query_seconds: int
    parser_version: str
    chunker_version: str
    tokenizer_version: str
    query_version: str
    scoring_version: str
    ranking_version: str

    @property
    def digest(self) -> str: ...
    def canonical_bytes(self) -> bytes: ...


def validate_lexical_configuration(config: LexicalConfiguration) -> None:
    config.canonical_bytes()
    if (
        config.parser_version,
        config.chunker_version,
        config.tokenizer_version,
        config.query_version,
        config.scoring_version,
        config.ranking_version,
    ) != (
        PARSER_VERSION,
        CHUNKER_VERSION,
        TOKENIZER_VERSION,
        QUERY_VERSION,
        SCORING_VERSION,
        RANKING_VERSION,
    ):
        raise ValueError("unsupported_lexical_configuration")


@dataclass(frozen=True)
class LexicalChunk:
    source: ChunkInput
    symbol: str | None
    terms: tuple[str, ...]


@dataclass(frozen=True)
class LexicalPlan:
    config: LexicalConfiguration
    manifest: IndexManifest
    chunks: tuple[LexicalChunk, ...]
    limitations: tuple[StageIssue, ...]

    @property
    def chunks_by_range(self) -> dict[tuple[str, int, int], LexicalChunk]:
        return {(c.source.path, c.source.line_start, c.source.line_end): c for c in self.chunks}


def tokenize(value: str) -> tuple[str, ...]:
    terms = set()
    for word in re.findall(r"\w+", value, flags=re.UNICODE):
        terms.add(word.casefold())
        split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", word).replace("_", " ")
        terms.update(part.casefold() for part in split.split())
    return tuple(sorted(terms))


def _lines(raw: bytes) -> list[bytes]:
    # Only CR, LF and CRLF are physical line boundaries; never Unicode/VT/FF.
    parts = re.split(rb"(\r\n|\r|\n)", raw)
    return [
        parts[i] + (parts[i + 1] if i + 1 < len(parts) else b"")
        for i in range(0, len(parts), 2)
        if parts[i] or i + 1 < len(parts)
    ]


def build_lexical_plan(snapshot: FrozenSnapshot, config: LexicalConfiguration) -> LexicalPlan:
    """Complete eligible corpus or fail; exclusions are explicit scoped limitations."""
    validate_frozen_snapshot(snapshot)
    validate_lexical_configuration(config)
    deadline = monotonic() + config.build_seconds
    chunks, limitations = [], []
    total = 0

    def append_chunk(path: str, first: int, end: int, content: bytes, symbol: str | None) -> None:
        nonlocal total
        total += len(content)
        if len(chunks) >= config.index_chunks or total > config.index_bytes:
            raise ValueError("lexical_index_limit")
        chunks.append(
            LexicalChunk(
                ChunkInput(path, first, end, content),
                symbol,
                tokenize(path + " " + (symbol or "") + " " + content.decode("utf-8")),
            )
        )

    for entry, raw in zip(snapshot.manifest.files, snapshot.contents, strict=True):
        if monotonic() >= deadline:
            raise ValueError("lexical_build_timeout")
        if exclusion_reason(entry.path, raw) is not None:
            limitations.append(StageIssue(code="index_policy_exclusion", path=entry.path))
            continue
        # Eligibility above already rejects binary/non-UTF8 contents.
        text = raw.decode("utf-8", errors="strict")
        symbols = (
            inspect_python(text).symbols if entry.path.casefold().endswith((".py", ".pyi")) else ()
        )
        lines = _lines(raw)
        labels = [None] * len(lines)
        # Parent spans label uncovered lines; smaller/nested symbols take precedence.
        for symbol in sorted(symbols, key=lambda s: (-(s.end - s.start), s.start, s.name)):
            labels[symbol.start - 1 : symbol.end] = [symbol.name] * (symbol.end - symbol.start + 1)
        start, pieces, label = 1, [], None

        size = 0
        for number, (line, symbol) in enumerate(zip(lines, labels, strict=True), start=1):
            if monotonic() >= deadline:
                raise ValueError("lexical_build_timeout")
            if len(line) > config.chunk_bytes:
                raise ValueError("lexical_line_limit")
            if pieces and (
                symbol != label
                or len(pieces) >= config.chunk_lines
                or size + len(line) > config.chunk_bytes
            ):
                append_chunk(entry.path, start, number - 1, b"".join(pieces), label)
                start, pieces, size = number, [], 0
            if not pieces:
                label = symbol
            pieces.append(line)
            size += len(line)
        if pieces:
            append_chunk(entry.path, start, len(lines), b"".join(pieces), label)
    manifest = build_index_manifest(
        snapshot,
        [c.source for c in chunks],
        index_version=INDEX_VERSION,
        configuration_id=config.digest,
    )
    plan = LexicalPlan(config, manifest, tuple(chunks), tuple(limitations))
    if monotonic() >= deadline:
        raise ValueError("lexical_build_timeout")
    return plan


def query_for_changes(
    changes: ChangePayload, config: LexicalConfiguration
) -> tuple[tuple[str, ...], bool]:
    terms = set()
    for component in changes.components:
        terms.update(tokenize(component.path + " " + (component.symbol or "")))
        if component.symbol and len(component.symbol) <= 256:
            terms.add(component.symbol.casefold())
        module = component.path.removesuffix(".py").replace("/", ".").casefold()
        if len(module) <= 256:
            terms.add(module)
    for file in changes.files:
        terms.update(tokenize(file.path))
    bounded = {term for term in terms if len(term) <= 256}
    return tuple(sorted(bounded)[: config.query_terms]), (
        len(bounded) > config.query_terms or bounded != terms
    )


def search_lexical(
    plan: LexicalPlan,
    snapshot: FrozenSnapshot,
    *,
    terms: tuple[str, ...],
    changes: ChangePayload | None = None,
    impact: ImpactPayload | None = None,
) -> StageResult[RetrievalPayload]:
    """Pure search over verified bytes, not proof of persisted-ready publication."""
    config = plan.config
    validate_lexical_configuration(config)
    deadline = monotonic() + config.query_seconds
    validate_index_manifest(
        snapshot, plan.manifest, index_version=INDEX_VERSION, configuration_id=config.digest
    )
    query = set(terms)
    if len(query) > config.query_terms or any(type(t) is not str or len(t) > 256 for t in query):
        raise ValueError("lexical_query_limit")
    identity = SnapshotIdentity(
        repository_id=plan.manifest.repository_id,
        commit=plan.manifest.commit,
        snapshot_id=plan.manifest.snapshot_id,
    )
    source = RetrievalSource(
        snapshot=identity, index_id=plan.manifest.index_id, configuration_id=config.digest
    )
    metadata = {(c.source.path, c.source.line_start, c.source.line_end): c for c in plan.chunks}
    items = []
    for chunk in plan.manifest.chunks:
        if monotonic() >= deadline:
            raise ValueError("lexical_query_timeout")
        value = metadata[(chunk.path, chunk.line_start, chunk.line_end)]
        matched = query.intersection(value.terms)
        if not matched:
            continue
        score = len(matched) + 4 * int((value.symbol or "").casefold() in query)
        score += 2 * int(chunk.path.rsplit(".", 1)[0].replace("/", ".").casefold() in query)
        items.append(
            RetrievalItem(
                snapshot=identity,
                index_id=source.index_id,
                configuration_id=source.configuration_id,
                id=chunk.chunk_id,
                path=chunk.path,
                location=dict(line_start=chunk.line_start, line_end=chunk.line_end),
                content_sha256=chunk.content_sha256,
                rank=len(items) + 1,
                score=float(score),
            )
        )
    # Input ranks must not accidentally defeat the specified physical stable tie-break.
    items.sort(key=lambda i: (i.path, i.location.line_start, i.location.line_end, i.id))
    items = [i.model_copy(update={"rank": rank}) for rank, i in enumerate(items, 1)]
    ranked = rank_and_validate_context(
        snapshot,
        RetrievalPayload(sources=[source], items=items),
        changes=changes,
        impact=impact,
        strict=True,
    )
    selected, size = [], 0
    for item in ranked.payload.items:
        value = metadata[(item.path, item.location.line_start, item.location.line_end)]
        if (
            len(selected) >= config.context_chunks
            or size + len(value.source.content) > config.context_bytes
        ):
            break
        selected.append(item)
        size += len(value.source.content)
    limitations = list(plan.limitations)
    if len(selected) < len(ranked.payload.items):
        limitations.append(StageIssue(code="retrieval_context_limit"))
    if monotonic() >= deadline:
        raise ValueError("lexical_query_timeout")
    return StageResult(
        status="partial" if limitations else "completed",
        data=ranked.payload.model_copy(update={"items": selected}),
        limitations=limitations,
    )

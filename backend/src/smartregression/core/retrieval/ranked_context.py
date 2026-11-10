"""Deterministic, validated, deduplicated, and ranked context for SmartRegression.

Rule version: 2.12-v1
AC requirements:
- Ranking/tie-break: Fully deterministic and auditable. Priority by relevance tier
  (Tier 1: directly changed, Tier 2: direct dependents, Tier 3: indirect dependents,
  Tier 4: other candidate/retrieved context), then score descending, then best
  original rank ascending, and alphabetical/numerical tie-break by path and span.
- Deduplication: Chunks with identical physical location and content hash are merged
  into a single ranked entry without losing provenance (all original sources, item IDs,
  ranks, and scores are retained).
- Validation: Verifies repository, commit, and snapshot identity against an immutable
  FrozenSnapshot (from Task 2.15). Verifies path existence in snapshot, source line
  ranges, and re-computes SHA256 of physical range bytes against content_sha256.
- Reject / Expose partial: Identity mismatches fail closed immediately. Corrupted or
  unresolvable chunks are either rejected (strict=True) or exposed as limitations in a
  partial StageResult (strict=False).
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from smartregression.contracts.stages import (
    ChangePayload,
    ImpactPayload,
    RetrievalItem,
    RetrievalPayload,
    RetrievalSource,
    SourceLocation,
    StageComponent,
    StageIssue,
    StageResult,
)
from smartregression.core.git.snapshots import (
    FrozenSnapshot,
    validate_frozen_snapshot,
    validate_snapshot_paths,
)
from smartregression.core.impact.changed_components import ComponentChange
from smartregression.core.retrieval.index_manifest import _PhysicalLines, _range_bytes

RULE_VERSION = "2.12-v1"


def extract_range_bytes(content: bytes, line_start: int, line_end: int) -> bytes:
    """Extract physical source line range bytes matching index_manifest convention."""
    return _range_bytes(content, line_start, line_end)


@dataclass(frozen=True)
class ContextProvenance:
    """Retains origin metadata when multiple retrieval entries are merged/deduplicated."""

    source: RetrievalSource
    original_item_id: str
    original_rank: int
    score: float | None = None


@dataclass(frozen=True)
class ValidatedContextItem:
    """A single deterministic validated, deduplicated, and ranked context item."""

    id: str
    path: str
    line_start: int
    line_end: int
    content_sha256: str
    rank: int
    tier: int
    score: float | None
    primary_source: RetrievalSource
    provenance: tuple[ContextProvenance, ...]


@dataclass(frozen=True)
class ValidatedContextResult:
    """Result of context validation, deduplication, and ranking."""

    status: Literal["completed", "partial"]
    payload: RetrievalPayload
    items: tuple[ValidatedContextItem, ...]
    limitations: tuple[StageIssue, ...]
    rule_version: str = RULE_VERSION

    def to_stage_result(self) -> StageResult[RetrievalPayload]:
        """Convert to canonical StageResult[RetrievalPayload] for stage report pipelines."""
        return StageResult[RetrievalPayload](
            status=self.status,
            data=self.payload,
            limitations=list(self.limitations),
        )


def _extract_relevance_tiers(
    changes: ChangePayload | Sequence[ComponentChange] | Sequence[StageComponent] | None,
    impact: ImpactPayload | None,
) -> tuple[set[str], set[str], set[str]]:
    """Partition paths into changed (Tier 1), direct (Tier 2), and indirect (Tier 3)."""
    changed_paths: set[str] = set()
    direct_paths: set[str] = set()
    indirect_paths: set[str] = set()

    if changes is not None:
        components: Sequence[ComponentChange | StageComponent]
        if isinstance(changes, ChangePayload):
            components = changes.components
        else:
            components = changes

        for comp in components:
            if comp.change in {"added", "modified", "renamed"}:
                changed_paths.add(comp.path)
                if comp.previous_path is not None:
                    changed_paths.add(comp.previous_path)

    if impact is not None:
        for candidate in impact.candidates:
            if candidate.relationship == "changed":
                changed_paths.add(candidate.path)
            elif candidate.relationship == "direct":
                direct_paths.add(candidate.path)
            elif candidate.relationship == "indirect":
                indirect_paths.add(candidate.path)

    # Disjoint priority tiers: Tier 1 > Tier 2 > Tier 3
    direct_paths -= changed_paths
    indirect_paths -= changed_paths | direct_paths

    return changed_paths, direct_paths, indirect_paths


def rank_and_validate_context(
    snapshot: FrozenSnapshot,
    payload: RetrievalPayload | Sequence[RetrievalPayload],
    *,
    changes: ChangePayload | Sequence[ComponentChange] | Sequence[StageComponent] | None = None,
    impact: ImpactPayload | None = None,
    strict: bool = False,
) -> ValidatedContextResult:
    """Validate, deduplicate, and deterministically rank retrieval context against snapshot.

    Args:
        snapshot: The immutable, verified FrozenSnapshot (Task 2.15).
        payload: One or more RetrievalPayload instances (from Task 2.11).
        changes: Optional change mapping (Task 2.01) to assign Tier 1 priority.
        impact: Optional reverse-reachable impact (Task 2.04) to assign Tiers 1-3.
        strict: If True, reject unresolvable/corrupted items with ValueError.
                If False, record issues in limitations and emit a partial result.

    Returns:
        ValidatedContextResult with deterministic ranking, deduplication provenance,
        validated payload, and any discovered limitations.
    """
    validate_frozen_snapshot(snapshot)

    payloads: list[RetrievalPayload]
    if isinstance(payload, RetrievalPayload):
        payloads = [payload]
    elif isinstance(payload, Sequence):
        payloads = list(payload)
    else:
        raise ValueError("invalid_retrieval_payload_input")

    if not payloads:
        raise ValueError("retrieval_payload_required")

    snapshot_repo = snapshot.manifest.repository_id
    snapshot_commit = snapshot.manifest.commit
    snapshot_id = snapshot.manifest.snapshot_id

    # Validate high-level snapshot identity across all sources
    all_input_sources: list[RetrievalSource] = []
    known_source_keys: set[tuple[object, str, str]] = set()

    for p in payloads:
        for src in p.sources:
            if src.snapshot.repository_id != snapshot_repo:
                raise ValueError("retrieval_repository_mismatch")
            if src.snapshot.commit != snapshot_commit:
                raise ValueError("retrieval_commit_mismatch")
            if src.snapshot.snapshot_id != snapshot_id:
                raise ValueError("retrieval_snapshot_mismatch")

            key = (src.snapshot, src.index_id, src.configuration_id)
            if key not in known_source_keys:
                known_source_keys.add(key)
                all_input_sources.append(src)

    # Map snapshot files for byte-level verification
    snapshot_files: dict[str, bytes] = {
        entry.path: content
        for entry, content in zip(snapshot.manifest.files, snapshot.contents, strict=True)
    }

    changed_paths, direct_paths, indirect_paths = _extract_relevance_tiers(changes, impact)

    # Track discovered issues
    limitations: list[StageIssue] = []
    seen_limitations: set[tuple[str, str | None]] = set()

    def add_limitation(code: str, path: str | None) -> None:
        key = (code, path)
        if key not in seen_limitations:
            seen_limitations.add(key)
            safe_path = None
            if path is not None:
                try:
                    validate_snapshot_paths([path])
                    safe_path = path
                except ValueError:
                    safe_path = None
            limitations.append(StageIssue(code=code, path=safe_path))

    # Validate items individually
    valid_items: list[tuple[RetrievalItem, RetrievalSource]] = []
    ranges: dict[str, _PhysicalLines] = {}

    for p in payloads:
        source_keys_in_payload = {
            (src.snapshot, src.index_id, src.configuration_id) for src in p.sources
        }
        for item in p.items:
            # Identity and provenance checks
            if item.snapshot.repository_id != snapshot_repo:
                raise ValueError("retrieval_repository_mismatch")
            if item.snapshot.commit != snapshot_commit:
                raise ValueError("retrieval_commit_mismatch")
            if item.snapshot.snapshot_id != snapshot_id:
                raise ValueError("retrieval_snapshot_mismatch")

            item_source_key = (item.snapshot, item.index_id, item.configuration_id)
            if item_source_key not in source_keys_in_payload:
                raise ValueError("retrieval_provenance_mismatch")

            source = RetrievalSource(
                snapshot=item.snapshot,
                index_id=item.index_id,
                configuration_id=item.configuration_id,
            )

            # File existence check
            content = snapshot_files.get(item.path)
            if content is None:
                if strict:
                    raise ValueError("unknown_snapshot_path")
                add_limitation("unknown_snapshot_path", item.path)
                continue

            # Source range check
            try:
                if item.path not in ranges:
                    ranges[item.path] = _PhysicalLines(content)
                range_bytes = ranges[item.path].range_bytes(
                    item.location.line_start, item.location.line_end
                )
            except ValueError as exc:
                if strict:
                    raise ValueError("invalid_source_range") from exc
                add_limitation("invalid_source_range", item.path)
                continue

            # Content hash check
            computed_sha = hashlib.sha256(range_bytes).hexdigest()
            if computed_sha != item.content_sha256:
                if strict:
                    raise ValueError("chunk_content_mismatch")
                add_limitation("chunk_content_mismatch", item.path)
                continue

            valid_items.append((item, source))

    # Deduplicate items by physical chunk identity: (path, line_start, line_end, content_sha256)
    # Group preserving all provenance
    grouped: dict[tuple[str, int, int, str], list[tuple[RetrievalItem, RetrievalSource]]] = {}
    for item, src in valid_items:
        chunk_key = (
            item.path,
            item.location.line_start,
            item.location.line_end,
            item.content_sha256,
        )
        grouped.setdefault(chunk_key, []).append((item, src))

    # Build deduplicated intermediate items
    intermediate_items: list[
        tuple[int, tuple[int, float], int, str, int, int, str, ValidatedContextItem]
    ] = []

    for (path, line_start, line_end, content_sha256), group in grouped.items():
        # Relevance tier
        if path in changed_paths:
            tier = 1
        elif path in direct_paths:
            tier = 2
        elif path in indirect_paths:
            tier = 3
        else:
            tier = 4

        # Provenance collection
        prov_list: list[ContextProvenance] = []
        for it, src in group:
            prov_list.append(
                ContextProvenance(
                    source=src,
                    original_item_id=it.id,
                    original_rank=it.rank,
                    score=it.score,
                )
            )

        # Best score: max of scores, or None if none present
        scores = [it.score for it, _ in group if it.score is not None]
        best_score = max(scores) if scores else None

        # Best original rank
        best_orig_rank = min(it.rank for it, _ in group)

        # Primary source selection:
        # Sort group to pick the representative item deterministically:
        # 1) score descending (if present), 2) original rank ascending, 3) item ID ascending
        rep_item, rep_source = min(
            group,
            key=lambda pair: (
                0 if pair[0].score is not None else 1,
                -(pair[0].score or 0.0),
                pair[0].rank,
                pair[0].id,
            ),
        )

        val_item = ValidatedContextItem(
            id=rep_item.id,
            path=path,
            line_start=line_start,
            line_end=line_end,
            content_sha256=content_sha256,
            rank=0,  # will be assigned after final sorting
            tier=tier,
            score=best_score,
            primary_source=rep_source,
            provenance=tuple(prov_list),
        )

        # Sort key components:
        # 1. Tier ascending (1 -> 2 -> 3 -> 4)
        # 2. Score descending: (0, -score) if present, else (1, 0.0)
        # 3. Best original rank ascending
        # 4. Path alphabetical
        # 5. line_start ascending
        # 6. line_end ascending
        # 7. id alphabetical
        score_key = (0, -best_score) if best_score is not None else (1, 0.0)
        sort_tuple = (
            tier,
            score_key,
            best_orig_rank,
            path,
            line_start,
            line_end,
            rep_item.id,
            val_item,
        )
        intermediate_items.append(sort_tuple)

    # Sort deterministically
    intermediate_items.sort(key=lambda t: t[:7])

    # Assign sequential ranks 1..N
    final_validated_items: list[ValidatedContextItem] = []
    final_retrieval_items: list[RetrievalItem] = []

    for rank, item_entry in enumerate(intermediate_items, start=1):
        raw_val = item_entry[7]
        ranked_val = ValidatedContextItem(
            id=raw_val.id,
            path=raw_val.path,
            line_start=raw_val.line_start,
            line_end=raw_val.line_end,
            content_sha256=raw_val.content_sha256,
            rank=rank,
            tier=raw_val.tier,
            score=raw_val.score,
            primary_source=raw_val.primary_source,
            provenance=raw_val.provenance,
        )
        final_validated_items.append(ranked_val)

        final_retrieval_items.append(
            RetrievalItem(
                snapshot=raw_val.primary_source.snapshot,
                index_id=raw_val.primary_source.index_id,
                configuration_id=raw_val.primary_source.configuration_id,
                id=raw_val.id,
                path=raw_val.path,
                location=SourceLocation(
                    line_start=raw_val.line_start,
                    line_end=raw_val.line_end,
                ),
                content_sha256=raw_val.content_sha256,
                rank=rank,
                score=raw_val.score,
            )
        )

    # Ensure all sources from input and items are retained in final payload sources
    source_map: dict[tuple[object, str, str], RetrievalSource] = {}
    for src in all_input_sources:
        key = (src.snapshot, src.index_id, src.configuration_id)
        source_map[key] = src

    for val in final_validated_items:
        for prov in val.provenance:
            key = (prov.source.snapshot, prov.source.index_id, prov.source.configuration_id)
            if key not in source_map:
                source_map[key] = prov.source

    # Sort sources canonically by index_id and configuration_id for determinism
    sorted_sources = sorted(
        source_map.values(),
        key=lambda s: (s.index_id, s.configuration_id),
    )

    final_payload = RetrievalPayload(
        sources=sorted_sources,
        items=final_retrieval_items,
    )

    status: Literal["completed", "partial"] = "partial" if limitations else "completed"

    return ValidatedContextResult(
        status=status,
        payload=final_payload,
        items=tuple(final_validated_items),
        limitations=tuple(limitations),
        rule_version=RULE_VERSION,
    )


def validate_retrieval_stage(
    snapshot: FrozenSnapshot,
    payload: RetrievalPayload | Sequence[RetrievalPayload],
    *,
    changes: ChangePayload | Sequence[ComponentChange] | Sequence[StageComponent] | None = None,
    impact: ImpactPayload | None = None,
    strict: bool = False,
) -> StageResult[RetrievalPayload]:
    """Validate and rank context, returning a canonical StageResult[RetrievalPayload]."""
    result = rank_and_validate_context(
        snapshot,
        payload,
        changes=changes,
        impact=impact,
        strict=strict,
    )
    return result.to_stage_result()

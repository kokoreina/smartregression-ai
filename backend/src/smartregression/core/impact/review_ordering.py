"""Deterministic manual-review ordering for changed components and their dependents.

Rule version: 2.07-v1
Output is ordered review starting points for human review only.
This module does NOT select tests, estimate fault probability, or assign fault labels.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from smartregression.contracts.models import ChangedComponent

RULE_VERSION = "2.07-v1"

# Limitations added when graph information is absent or incomplete.
_LIMITATION_PARTIAL_GRAPH = "partial_graph"


@dataclass(frozen=True)
class ReviewCandidate:
    """A single component recommended for manual review.

    Tier semantics:
        1 — directly changed executable (source of truth: ChangedComponent list)
        2 — direct dependent (imports a Tier-1 component)
        3 — indirect dependent (transitively reachable, not Tier 1 or 2)

    ``symbol`` is ``None`` when the finding is at file/module level.
    No confidence score, no fault label.
    """

    path: str
    symbol: str | None
    tier: Literal[1, 2, 3]
    reason: str


@dataclass(frozen=True)
class ReviewOrder:
    """Final ordered list of review candidates with provenance.

    ``candidates`` is sorted: tier ascending, then (path, symbol or "") ascending
    for stable deterministic output even when ties exist.
    ``limitations`` collects both caller-supplied limitations and those discovered
    during ordering (e.g. partial_graph when edges are absent).
    ``rule_version`` pins the algorithm for traceability.
    """

    candidates: tuple[ReviewCandidate, ...]
    limitations: tuple[str, ...]
    rule_version: str


def order_for_review(
    changed: Sequence[ChangedComponent],
    edges: Sequence[tuple[str, str]],
    limitations: Sequence[str],
) -> ReviewOrder:
    """Produce a deterministic, deduplicated ordered list of review candidates.

    Args:
        changed:     Changed components from task 2.01. Each contributes a Tier-1 entry.
        edges:       Directed import edges as (importer_path, importee_path) pairs,
                     as produced by ``module_edges`` from task 2.03/python_snapshot.
                     An empty sequence signals a partial graph.
        limitations: Caller-supplied limitation strings (e.g. from 2.17 partial parsing).
                     These are preserved verbatim and merged with internally discovered ones.

    Returns:
        ReviewOrder with candidates sorted by (tier, path, symbol), limitations merged,
        and rule_version = RULE_VERSION.

    Ordering rules (2.07-v1):
        - Tier 1: every path/symbol in ``changed`` that is an executable component.
        - Tier 2: every importer whose path appears as an importer in ``edges`` and
          whose importee path is a Tier-1 path; excluding paths already in Tier 1.
        - Tier 3: transitive importers reachable from Tier 1 via BFS; excluding Tier 1/2.
        - Dedup: if a path is promoted to a lower tier number, remove its higher-tier entry.
        - Stable ties: within a tier, sort ascending by (path, symbol or "").
        - Cycle safety: BFS with visited set; no path is visited twice.
    """
    extra_limitations: set[str] = set()

    # --- Tier 1 ---
    # Assign each changed component with path + optional symbol.
    tier1_paths: set[str] = set()
    tier1_candidates: list[ReviewCandidate] = []
    for comp in changed:
        key = (comp.path, comp.symbol)
        if key not in {(c.path, c.symbol) for c in tier1_candidates}:
            tier1_candidates.append(
                ReviewCandidate(
                    path=comp.path,
                    symbol=comp.symbol,
                    tier=1,
                    reason=f"directly changed ({comp.change})",
                )
            )
        tier1_paths.add(comp.path)

    # --- Build adjacency: importee_path → set of importer_paths ---
    # Edge direction: (importer, importee) means importer depends on importee.
    # We want to find who depends on (imports) a Tier-1 path, so we index by importee.
    if not edges:
        extra_limitations.add(_LIMITATION_PARTIAL_GRAPH)

    dependents_of: dict[str, set[str]] = {}  # importee_path → importer_paths
    for importer, importee in edges:
        dependents_of.setdefault(importee, set()).add(importer)

    # --- Tier 2: direct importers of Tier-1 paths ---
    tier2_paths: set[str] = set()
    tier2_candidates: list[ReviewCandidate] = []
    for t1_path in sorted(tier1_paths):  # sorted for determinism
        for importer in sorted(dependents_of.get(t1_path, set())):
            if importer not in tier1_paths and importer not in tier2_paths:
                tier2_paths.add(importer)
                tier2_candidates.append(
                    ReviewCandidate(
                        path=importer,
                        symbol=None,
                        tier=2,
                        reason=f"directly imports changed path '{t1_path}'",
                    )
                )

    # --- Tier 3: transitive importers (BFS from Tier-1, skipping Tier 1+2) ---
    tier3_paths: set[str] = set()
    tier3_candidates: list[ReviewCandidate] = []
    visited: set[str] = set(tier1_paths) | tier2_paths
    frontier: list[str] = list(sorted(tier2_paths))  # BFS starts from Tier 2
    while frontier:
        next_frontier: list[str] = []
        for current in frontier:
            for importer in sorted(dependents_of.get(current, set())):
                if importer not in visited:
                    visited.add(importer)
                    tier3_paths.add(importer)
                    tier3_candidates.append(
                        ReviewCandidate(
                            path=importer,
                            symbol=None,
                            tier=3,
                            reason=f"transitively depends on '{current}'",
                        )
                    )
                    next_frontier.append(importer)
        frontier = next_frontier

    # --- Merge and sort ---
    all_candidates = tier1_candidates + tier2_candidates + tier3_candidates

    def sort_key(c: ReviewCandidate) -> tuple[int, str, str]:
        return (c.tier, c.path, c.symbol or "")

    sorted_candidates = tuple(sorted(all_candidates, key=sort_key))

    # --- Merge limitations ---
    merged_limitations = tuple(sorted(set(limitations) | extra_limitations))

    return ReviewOrder(
        candidates=sorted_candidates,
        limitations=merged_limitations,
        rule_version=RULE_VERSION,
    )

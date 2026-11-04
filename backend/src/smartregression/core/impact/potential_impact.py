"""Reverse-reachable static potential impact analysis."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Literal

from smartregression.contracts.stages import (
    ChangePayload,
    GraphPayload,
    ImpactCandidate,
    ImpactPath,
    ImpactPayload,
    RunIdentity,
    StageComponent,
    validate_artifacts,
)
from smartregression.core.git.snapshots import canonical_json


def _identifier(kind: str, value: object) -> str:
    return hashlib.sha256(canonical_json({"kind": kind, "value": value})).hexdigest()


def _selected_path(component: StageComponent, *, is_base: bool) -> str | None:
    if is_base:
        if component.change == "added":
            return None
        return component.previous_path or component.path
    if component.change == "deleted":
        return None
    return component.path


def _simple_reverse_paths(
    origin: str, reverse_dependencies: dict[str, tuple[str, ...]]
) -> tuple[tuple[str, ...], ...]:
    """Return every simple path from an importer to ``origin``."""

    found: set[tuple[str, ...]] = set()

    def visit(current: str, path_from_candidate: tuple[str, ...]) -> None:
        for importer in reverse_dependencies.get(current, ()):
            if importer in path_from_candidate:
                continue
            candidate_path = (importer, *path_from_candidate)
            found.add(candidate_path)
            visit(importer, candidate_path)

    visit(origin, (origin,))
    return tuple(sorted(found, key=lambda path: (len(path), path)))


def _reverse_dependencies(graph: GraphPayload) -> dict[str, tuple[str, ...]]:
    reverse: dict[str, set[str]] = {}
    for edge in graph.edges:
        if edge.source != edge.target:
            reverse.setdefault(edge.target, set()).add(edge.source)
    return {target: tuple(sorted(importers)) for target, importers in reverse.items()}


def _candidate(
    component: StageComponent,
    path: str,
    relationship: Literal["changed", "direct", "indirect"],
    path_ids: Iterable[str],
) -> ImpactCandidate:
    path_ids = tuple(path_ids)
    return ImpactCandidate(
        id=_identifier(
            "impact_candidate",
            {
                "changed_component_id": component.id,
                "path": path,
                "symbol": component.symbol if relationship == "changed" else None,
                "relationship": relationship,
            },
        ),
        path=path,
        symbol=component.symbol if relationship == "changed" else None,
        relationship=relationship,
        changed_component_id=component.id,
        path_ids=list(path_ids),
        explanation="Static import reachability indicates potential impact only.",
    )


def build_potential_impact(
    identity: RunIdentity,
    changes: ChangePayload,
    graph: GraphPayload,
) -> ImpactPayload:
    """Build deterministic reverse-reachable candidates for one graph snapshot."""

    if graph.snapshot not in (identity.base, identity.target):
        raise ValueError("graph_snapshot_mismatch")

    is_base = graph.snapshot == identity.base
    graph_nodes = set(graph.nodes)
    reverse_dependencies = _reverse_dependencies(graph)
    graph_edges = {(edge.source, edge.target) for edge in graph.edges}
    candidates: list[ImpactCandidate] = []
    paths: list[ImpactPath] = []

    for component in sorted(changes.components, key=lambda item: item.id):
        origin = _selected_path(component, is_base=is_base)
        if origin is None:
            continue
        if origin not in graph_nodes:
            raise ValueError("changed_component_not_in_graph")

        candidates.append(_candidate(component, origin, "changed", ()))
        discovered = _simple_reverse_paths(origin, reverse_dependencies)
        path_records: list[tuple[str, tuple[str, ...]]] = []
        for nodes in discovered:
            path_id = _identifier(
                "impact_path",
                {"changed_component_id": component.id, "nodes": nodes},
            )
            path_records.append((path_id, nodes))
            paths.append(
                ImpactPath(id=path_id, changed_component_id=component.id, nodes=list(nodes))
            )

        by_candidate: dict[str, list[str]] = {}
        for path_id, nodes in path_records:
            by_candidate.setdefault(nodes[0], []).append(path_id)
        for candidate_path in sorted(by_candidate):
            candidate_paths = tuple(sorted(by_candidate[candidate_path]))
            relationship = "direct" if (candidate_path, origin) in graph_edges else "indirect"
            candidates.append(_candidate(component, candidate_path, relationship, candidate_paths))

    candidates.sort(key=lambda item: (item.path, item.symbol or "", item.changed_component_id))
    paths.sort(key=lambda item: (item.changed_component_id, len(item.nodes), tuple(item.nodes)))
    impact = ImpactPayload(snapshot=graph.snapshot, candidates=candidates, paths=paths)
    validate_artifacts(identity, changes, graph, impact, None)
    return impact

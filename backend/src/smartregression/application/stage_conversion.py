"""Boundary mappings, not workflow orchestration or algorithm implementations.

Callers authorize inputs and obtain sources from trusted frozen snapshots. Mappers
check declared identity; graph parsing alone cannot attest to source acquisition.
"""

import hashlib
from dataclasses import asdict

from smartregression.application.changed_components import ChangeAnalysis
from smartregression.contracts.models import ChangedComponent
from smartregression.contracts.stages import (
    ChangePayload,
    FileCoverage,
    GraphPayload,
    ImportLimitation,
    ReviewItem,
    ReviewPayload,
    RunIdentity,
    SnapshotIdentity,
    SnapshotPayload,
    StageComponent,
    StageEdge,
    StageIssue,
    StageResult,
)
from smartregression.core.git.snapshots import (
    FrozenSnapshot,
    SnapshotPair,
    canonical_json,
    validate_frozen_snapshot,
)
from smartregression.core.impact.dependency_graph import DependencyGraph
from smartregression.core.impact.review_ordering import ReviewOrder


def snapshots_result(pair: SnapshotPair) -> StageResult[SnapshotPayload]:
    for snapshot in (pair.base, pair.target):
        validate_frozen_snapshot(snapshot)

    def identity(snapshot: FrozenSnapshot) -> SnapshotIdentity:
        manifest = snapshot.manifest
        return SnapshotIdentity(
            repository_id=manifest.repository_id,
            commit=manifest.commit,
            snapshot_id=manifest.snapshot_id,
        )

    return StageResult[SnapshotPayload](
        status="completed",
        data=SnapshotPayload(base=identity(pair.base), target=identity(pair.target)),
    )


def identity_from_snapshots(pair: SnapshotPair, *, run_id: str) -> RunIdentity:
    """Hash-check a pair; this is not an authorization decision."""
    payload = snapshots_result(pair).data
    assert payload is not None
    return RunIdentity(
        repository_id=payload.base.repository_id,
        run_id=run_id,
        base=payload.base,
        target=payload.target,
        comparison_mode="direct_two_tree",
    )


def changes_result(result: ChangeAnalysis, identity: RunIdentity) -> StageResult[ChangePayload]:
    if (
        result.repository != identity.repository_id
        or result.base_sha != identity.base.commit
        or result.target_sha != identity.target.commit
        or result.comparison_mode != identity.comparison_mode
        or result.schema_version != "changed-components/1"
        or result.status not in {"completed", "partial"}
    ):
        raise ValueError("change_identity_or_version_mismatch")
    records = []
    for component in result.components:
        fields = asdict(component)
        component_id = hashlib.sha256(canonical_json(fields)).hexdigest()
        records.append(StageComponent(id=component_id, **fields))
    issues = [
        StageIssue(code=reason, path=f.path) for f in result.files for reason in f.limitations
    ]
    # file_only is a known scope limitation, not a Python parse failure.
    status = "partial" if issues or result.status == "partial" else "completed"
    if result.status == "partial" and not issues:
        issues.append(StageIssue(code="producer_partial"))
    return StageResult[ChangePayload](
        status=status,
        data=ChangePayload(
            components=records, files=[FileCoverage(**asdict(f)) for f in result.files]
        ),
        limitations=issues,
    )


def graph_result(graph: DependencyGraph, snapshot: SnapshotIdentity) -> StageResult[GraphPayload]:
    # Recheck every endpoint, including forged dataclasses and an otherwise empty graph.
    nodes = [*graph.nodes, *(e.source for e in graph.edges), *(e.target for e in graph.edges)]
    if any(n.repository != snapshot.repository_id or n.revision != snapshot.commit for n in nodes):
        raise ValueError("graph_snapshot_mismatch")
    issues = [StageIssue(code=u.reason, path=u.source_path) for u in graph.unresolved]
    return StageResult[GraphPayload](
        status="partial" if issues else "completed",
        data=GraphPayload(
            snapshot=snapshot,
            nodes=[n.path for n in graph.nodes],
            edges=[
                StageEdge(source=e.source.path, target=e.target.path, kind=e.kind)
                for e in graph.edges
            ],
            unresolved=[ImportLimitation(**asdict(u)) for u in graph.unresolved],
        ),
        limitations=issues,
    )


def ordering_inputs(
    changes: StageResult[ChangePayload],
    graph: StageResult[GraphPayload],
    identity: RunIdentity,
) -> tuple[list[ChangedComponent], list[tuple[str, str]], list[str]]:
    """Explicit lossy projection for legacy 2.07; keep canonical payloads in report.

    Only parsed Python executable components seed this view. Deleted components
    can seed a base graph, additions a target graph. Container-only changes and
    non-executable metadata stay in changes, not in the 'direct executable' tier.
    No producer algorithm is modified. 2.13 must also check report-level scope.
    """
    if changes.data is None or graph.data is None:
        raise ValueError("ordering_prerequisite_unavailable")
    if graph.data.snapshot not in (identity.base, identity.target):
        raise ValueError("graph_snapshot_mismatch")
    is_base = graph.data.snapshot == identity.base
    limitations = {i.code for stage in (changes, graph) for i in stage.limitations}
    projected = []
    for c in changes.data.components:
        if not c.path.endswith(".py"):
            limitations.add("non_executable_changes_omitted")
            continue
        if c.kind == "file":
            # File-only parse failures must not be presented as parsed executables.
            continue
        if c.reason == "contains_changed_symbol":
            limitations.add("container_changes_omitted")
            continue
        if (is_base and c.change == "added") or (not is_base and c.change == "deleted"):
            limitations.add("components_absent_from_graph_revision")
            continue
        path = (c.previous_path or c.path) if is_base else c.path
        if path not in graph.data.nodes:
            limitations.add("changed_component_not_in_graph")
            continue
        projected.append(
            ChangedComponent(
                path=path,
                symbol=c.symbol,
                change=c.change,
                previous_path=c.previous_path if not is_base else None,
            )
        )
    edges = [(e.source, e.target) for e in graph.data.edges]
    return projected, edges, sorted(limitations)


def review_result(order: ReviewOrder, snapshot: SnapshotIdentity) -> StageResult[ReviewPayload]:
    return StageResult[ReviewPayload](
        status="partial" if order.limitations else "completed",
        data=ReviewPayload(
            snapshot=snapshot,
            rule_version=order.rule_version,
            candidates=[ReviewItem(**asdict(c)) for c in order.candidates],
        ),
        limitations=[StageIssue(code=code) for code in order.limitations],
    )

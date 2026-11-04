"""Frozen-source verification for deterministic static-impact explanations only."""

import hashlib

from smartregression.application.stage_conversion import identity_from_snapshots
from smartregression.contracts.stages import (
    ChangePayload,
    EvidenceBundle,
    EvidencePayload,
    GraphPayload,
    ImpactCandidate,
    ImpactPayload,
    RunIdentity,
    SnapshotIdentity,
    SourceLocation,
    StageComponent,
    StageEvidence,
    StageIssue,
    StageResult,
    validate_artifacts,
)
from smartregression.core.evidence.resolution import resolve_source, source_lines
from smartregression.core.git.snapshots import SnapshotPair, canonical_json
from smartregression.core.impact.dependency_graph import build_dependency_graph
from smartregression.core.impact.python_snapshot import MAX_PYTHON_SOURCE_BYTES, inspect_python

EVIDENCE_VERSION = "frozen-static-evidence/1"


class _Sources:
    def __init__(self, identity: RunIdentity, pair: SnapshotPair) -> None:
        if identity_from_snapshots(pair, run_id=identity.run_id) != identity:
            raise ValueError("evidence_snapshot_identity_mismatch")
        self.identity = identity
        self.files = {
            side: {
                entry.path: raw
                for entry, raw in zip(snapshot.manifest.files, snapshot.contents, strict=True)
            }
            for side, snapshot in (("base", pair.base), ("target", pair.target))
        }

    def side(self, snapshot: SnapshotIdentity) -> str:
        if snapshot == self.identity.base:
            return "base"
        if snapshot == self.identity.target:
            return "target"
        raise ValueError("foreign_evidence_snapshot")

    def raw(self, snapshot: SnapshotIdentity, path: str) -> bytes | None:
        return self.files[self.side(snapshot)].get(path)

    def text(self, side: str, path: str) -> str | None:
        raw = self.files[side].get(path)
        if raw is None:
            return None
        if len(raw) > MAX_PYTHON_SOURCE_BYTES or b"\0" in raw:
            raise ValueError("evidence_source_unsupported")
        return raw.decode("utf-8", errors="strict")

    def changed(self, component: StageComponent) -> bool | None:
        try:
            snippets = []
            for side in ("base", "target"):
                path = (
                    (component.previous_path or component.path)
                    if side == "base"
                    else component.path
                )
                text = self.text(side, path)
                location = getattr(component, side + "_location")
                if text is None:
                    snippets.append(None)
                elif component.symbol:
                    symbols = [
                        s for s in inspect_python(text).symbols if s.name == component.symbol
                    ]
                    if not symbols:
                        snippets.append(None)
                    elif (
                        len(symbols) != 1
                        or location is None
                        or (symbols[0].start, symbols[0].end)
                        != (location.line_start, location.line_end)
                    ):
                        return False
                    else:
                        snippets.append(
                            "\n".join(
                                source_lines(text)[location.line_start - 1 : location.line_end]
                            )
                        )
                else:
                    if location is not None and (
                        location.line_start != 1 or location.line_end != len(source_lines(text))
                    ):
                        return False
                    snippets.append(text)
            before, after = snippets
            if component.change == "added":
                return before is None and after is not None
            if component.change == "deleted":
                return before is not None and after is None
            if component.change == "renamed":
                return (
                    component.previous_path is not None and before is not None and after is not None
                )
            return before is not None and after is not None and before != after
        except ValueError, UnicodeError, RecursionError:
            return None

    def edges(self, graph: GraphPayload) -> set[tuple[str, str, str]] | None:
        try:
            side = self.side(graph.snapshot)
            actual = build_dependency_graph(
                repository=self.identity.repository_id,
                revision=graph.snapshot.commit,
                sources={
                    path: self.text(side, path) for path in self.files[side] if path.endswith(".py")
                },
            )
            return {(e.source.path, e.target.path, e.kind) for e in actual.edges}
        except ValueError, UnicodeError, RecursionError:
            return None


def _explanation(candidate: ImpactCandidate, supported: bool) -> str:
    if not supported:
        return "Static potential impact; source support is not verified."
    if candidate.relationship == "changed":
        return (
            "Changed source verified at the referenced base/target spans; "
            "behavioral effects are unknown."
        )
    return (
        "Static import reachability to the changed source verified; "
        "this is potential impact, not a proven behavioral change."
    )


def _stage(items: list[StageEvidence]) -> StageResult[EvidencePayload]:
    issues = sorted(
        {
            (e.verification_reason or "evidence_unverified", e.path)
            for e in items
            if e.resolution != "resolved" or e.support != "supported"
        }
    )
    return StageResult(
        status="partial" if issues else "completed",
        data=EvidencePayload(items=items),
        limitations=[StageIssue(code=code, path=path) for code, path in issues],
    )


def explain_impact(
    identity: RunIdentity,
    changes: ChangePayload,
    graph: GraphPayload,
    impact: ImpactPayload,
    pair: SnapshotPair,
) -> tuple[ImpactPayload, StageResult[EvidencePayload]]:
    """Generate claim-scoped witnesses; existing free-form explanation is never attested."""
    identity = RunIdentity.model_validate_json(identity.model_dump_json())
    changes = ChangePayload.model_validate_json(changes.model_dump_json())
    graph = GraphPayload.model_validate_json(graph.model_dump_json())
    impact = ImpactPayload.model_validate_json(impact.model_dump_json())
    # Existing references may be from an untrusted report; regenerate rather than trust them.
    impact = impact.model_copy(
        update={
            "candidates": [c.model_copy(update={"evidence_ids": []}) for c in impact.candidates]
        }
    )
    validate_artifacts(identity, changes, graph, impact, EvidencePayload(items=[]))
    sources = _Sources(identity, pair)
    edges = sources.edges(graph)
    components = {c.id: c for c in changes.components}
    paths = {p.id: p for p in impact.paths}
    candidates, items = [], []
    for candidate in impact.candidates:
        component = components[candidate.changed_component_id]
        witnesses = []
        for side in ("base", "target"):
            location = getattr(component, side + "_location")
            if location is None and component.kind == "file":
                try:
                    path = (
                        (component.previous_path or component.path)
                        if side == "base"
                        else component.path
                    )
                    text = sources.text(side, path)
                    count = len(source_lines(text)) if text is not None else 0
                    if count:
                        location = SourceLocation(line_start=1, line_end=count)
                except UnicodeError, ValueError:
                    pass  # No source location is fabricated for unsupported files.
            if location is not None:
                witnesses.append(
                    (
                        getattr(identity, side),
                        (component.previous_path or component.path)
                        if side == "base"
                        else component.path,
                        location,
                        component.symbol,
                    )
                )
        required = set()
        for path_id in candidate.path_ids:
            path = paths[path_id]
            required.update(zip(path.nodes, path.nodes[1:], strict=False))
            for source_path in path.nodes[:-1]:
                raw = sources.raw(graph.snapshot, source_path)
                try:
                    lines = source_lines(raw.decode("utf-8")) if raw is not None else []
                except UnicodeError:
                    lines = []
                witnesses.append(
                    (
                        graph.snapshot,
                        source_path,
                        SourceLocation(line_start=1, line_end=max(1, len(lines))),
                        None,
                    )
                )
        changed = sources.changed(component)
        edge_supported = (
            edges is not None
            and required <= {(a, b) for a, b, _ in edges}
            and all(
                (e.source, e.target, e.kind) in edges
                for e in graph.edges
                if (e.source, e.target) in required
            )
            and candidate.path.endswith(".py")
            and sources.raw(graph.snapshot, candidate.path) is not None
        )
        actual = []
        seen = set()
        for snapshot, path, location, symbol in witnesses:
            fields = dict(
                snapshot=snapshot.model_dump(mode="json"),
                path=path,
                location=location.model_dump(),
                symbol=symbol,
            )
            evidence_id = hashlib.sha256(
                canonical_json(
                    {
                        "producer": EVIDENCE_VERSION,
                        "candidate": candidate.id,
                        **fields,
                    }
                )
            ).hexdigest()
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            item = resolve_source(
                StageEvidence(id=evidence_id, **fields), sources.raw(snapshot, path)
            )
            actual.append(item)
        supported = (
            bool(actual)
            and changed is True
            and edge_supported
            and all(item.resolution == "resolved" for item in actual)
        )
        support = (
            "supported"
            if supported
            else "unverified"
            if changed is None or edges is None
            else "unsupported"
        )
        actual = [
            item.model_copy(
                update={
                    "support": support if item.resolution == "resolved" else "unverified",
                    "verification_reason": "static_claim_supported"
                    if supported
                    else (
                        "static_claim_unsupported"
                        if support == "unsupported"
                        else "static_claim_unverified"
                        if item.resolution == "resolved"
                        else item.verification_reason
                    ),
                }
            )
            for item in actual
        ]
        items.extend(actual)
        candidates.append(
            candidate.model_copy(
                update={
                    "evidence_ids": [item.id for item in actual],
                    "explanation": _explanation(candidate, supported),
                }
            )
        )
    explained = impact.model_copy(update={"candidates": candidates})
    validate_artifacts(identity, changes, graph, explained, EvidencePayload(items=items))
    result = _stage(items)
    if any(not c.evidence_ids for c in candidates):
        result = StageResult(
            status="partial",
            data=result.data,
            limitations=[*result.limitations, StageIssue(code="evidence_location_unavailable")],
        )
    return explained, result


def inspect_bundle(bundle: EvidenceBundle, pair: SnapshotPair) -> StageResult[EvidencePayload]:
    """Transient inspection; never modifies or persists the original saved producer claims."""
    checked = EvidenceBundle.model_validate_json(bundle.model_dump_json())
    sources = _Sources(checked.identity, pair)
    expected, stage = explain_impact(
        checked.identity, checked.changes, checked.graph, checked.impact, pair
    )
    expected_items = {item.id: item for item in stage.data.items}
    expected_candidates = {c.id: c for c in expected.candidates}
    allowed = set()
    for candidate in checked.impact.candidates:
        computed = expected_candidates[candidate.id]
        if (
            candidate.explanation == computed.explanation
            and candidate.evidence_ids == computed.evidence_ids
        ):
            allowed.update(candidate.evidence_ids)
    result = []
    for item in checked.evidence.items:
        actual = resolve_source(item, sources.raw(item.snapshot, item.path))
        witness = expected_items.get(item.id)
        if (
            actual.resolution == "resolved"
            and witness is not None
            and (item.id in allowed or witness.support == "unsupported")
            and (actual.snapshot, actual.path, actual.location, actual.symbol)
            == (witness.snapshot, witness.path, witness.location, witness.symbol)
        ):
            actual = actual.model_copy(
                update={
                    "support": witness.support,
                    "verification_reason": witness.verification_reason,
                }
            )
        result.append(actual)
    inspected = _stage(result)
    missing = set(expected_items) - {item.id for item in checked.evidence.items}
    if missing:
        return StageResult(
            status="partial",
            data=inspected.data,
            limitations=[*inspected.limitations, StageIssue(code="evidence_witness_missing")],
        )
    if stage.status == "partial" and inspected.status == "completed":
        return StageResult(status="partial", data=inspected.data, limitations=stage.limitations)
    return inspected

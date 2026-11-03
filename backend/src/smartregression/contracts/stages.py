"""Canonical Sprint 2 reports. Structural validation is not source verification.

Legacy models remain in models.py. Nested v2 values inherit the enclosing report
version; they do not inherit the legacy Contract's implicit 1.0.0 version.
"""

from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from smartregression.contracts.models import Commit, Text

Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Code = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$")]
StageStatus = Literal["not_implemented", "not_run", "completed", "partial", "failed"]


class StageValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceLocation(StageValue):
    line_start: int = Field(ge=1, strict=True)
    line_end: int = Field(ge=1, strict=True)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.line_end < self.line_start:
            raise ValueError("invalid_line_range")
        return self


def checked_path(value: str) -> str:
    # Same portable repository-relative namespace as the snapshot boundary.
    from smartregression.core.git.snapshots import validate_snapshot_paths

    validate_snapshot_paths([value])
    return value


RepoPath = Annotated[str, AfterValidator(checked_path)]
RepositoryId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")]


class SnapshotIdentity(StageValue):
    repository_id: RepositoryId
    commit: Commit
    # Required but nullable until materialization succeeds; never invent a hash.
    snapshot_id: Digest | None


def require_snapshot(snapshot: SnapshotIdentity) -> None:
    if snapshot.snapshot_id is None:
        raise ValueError("materialized_snapshot_required")


class RunIdentity(StageValue):
    repository_id: RepositoryId
    run_id: Text
    base: SnapshotIdentity
    target: SnapshotIdentity
    comparison_mode: Literal["direct_two_tree"]

    @model_validator(mode="after")
    def same_repository(self) -> Self:
        if any(s.repository_id != self.repository_id for s in (self.base, self.target)):
            raise ValueError("cross_repository_snapshot")
        if (
            self.base.commit == self.target.commit
            and self.base.snapshot_id is not None
            and self.target.snapshot_id is not None
            and self.base != self.target
        ):
            raise ValueError("same_commit_snapshot_mismatch")
        return self


class StageIssue(StageValue):
    code: Code
    path: RepoPath | None = None


class StageResult[T](StageValue):
    status: StageStatus
    data: T | None = None
    reason: Code | None = None
    limitations: list[StageIssue] = Field(default_factory=list)
    error_code: Code | None = None

    @model_validator(mode="after")
    def legal_state(self) -> Self:
        if self.status in {"completed", "partial"}:
            if self.data is None or self.error_code is not None or self.reason is not None:
                raise ValueError("invalid_success_payload")
            if self.status == "partial" and not self.limitations:
                raise ValueError("partial_requires_limitations")
            if self.status == "completed" and self.limitations:
                raise ValueError("limitations_require_partial_stage")
        else:
            if self.data is not None:
                raise ValueError("inactive_stage_has_payload")
            if self.status == "failed":
                if self.error_code is None or self.reason is not None:
                    raise ValueError("failed_requires_error_code")
            elif self.reason is None or self.error_code is not None:
                raise ValueError("inactive_stage_requires_reason")
        return self


class SnapshotPayload(StageValue):
    base: SnapshotIdentity
    target: SnapshotIdentity

    @model_validator(mode="after")
    def materialized(self) -> Self:
        require_snapshot(self.base)
        require_snapshot(self.target)
        if self.base.repository_id != self.target.repository_id:
            raise ValueError("cross_repository_snapshot")
        return self


class StageComponent(StageValue):
    id: Text
    path: RepoPath
    previous_path: RepoPath | None = None
    kind: Literal["file", "module", "class", "function", "method"]
    symbol: Text | None = None
    change: Literal["added", "modified", "deleted", "renamed"]
    base_location: SourceLocation | None = None
    target_location: SourceLocation | None = None
    reason: Code

    @model_validator(mode="after")
    def coherent_locations(self) -> Self:
        if self.kind == "file" and (
            self.base_location is not None or self.target_location is not None
        ):
            raise ValueError("file_metadata_has_source_location")
        if self.change == "added" and self.base_location is not None:
            raise ValueError("added_has_base_location")
        if self.change == "deleted" and self.target_location is not None:
            raise ValueError("deleted_has_target_location")
        if self.previous_path is not None and self.previous_path == self.path:
            raise ValueError("previous_path_unchanged")
        # Renamed files may contain added/deleted/modified symbols.
        if self.change == "renamed" and self.previous_path is None:
            raise ValueError("rename_requires_previous_path")
        if (self.kind in {"class", "function", "method"}) != (self.symbol is not None):
            raise ValueError("invalid_component_symbol")
        if self.kind in {"class", "function", "method"}:
            if self.change != "added" and self.base_location is None:
                raise ValueError("missing_base_location")
            if self.change != "deleted" and self.target_location is None:
                raise ValueError("missing_target_location")
        return self


class FileCoverage(StageValue):
    path: RepoPath
    status: Literal["completed", "partial", "file_only"]
    limitations: list[Code]

    @model_validator(mode="after")
    def incomplete_has_reason(self) -> Self:
        if self.status != "completed" and not self.limitations:
            raise ValueError("incomplete_file_requires_limitations")
        return self


def unique(values: list[object]) -> None:
    if len(values) != len(set(values)):
        raise ValueError("duplicate_reference")


class ChangePayload(StageValue):
    components: list[StageComponent]
    files: list[FileCoverage]

    @model_validator(mode="after")
    def references(self) -> Self:
        unique([c.id for c in self.components])
        unique([f.path for f in self.files])
        unique([(c.path, c.kind, c.symbol) for c in self.components])
        if {c.path for c in self.components} != {f.path for f in self.files}:
            raise ValueError("component_file_coverage_mismatch")
        return self


class StageEdge(StageValue):
    source: RepoPath
    target: RepoPath
    kind: Code


class ImportLimitation(StageValue):
    source_path: RepoPath
    reference: Text
    kind: Code
    reason: Code


class GraphPayload(StageValue):
    snapshot: SnapshotIdentity
    edge_direction: Literal["importer_to_importee"] = "importer_to_importee"
    nodes: list[RepoPath]
    edges: list[StageEdge]
    unresolved: list[ImportLimitation]

    @model_validator(mode="after")
    def endpoints(self) -> Self:
        require_snapshot(self.snapshot)
        unique(list(self.nodes))
        unique([(e.source, e.target, e.kind) for e in self.edges])
        nodes = set(self.nodes)
        if any(e.source not in nodes or e.target not in nodes for e in self.edges):
            raise ValueError("unknown_edge_endpoint")
        if any(u.source_path not in nodes for u in self.unresolved):
            raise ValueError("unknown_unresolved_source")
        return self


class ImpactPath(StageValue):
    id: Text
    changed_component_id: Text
    # Candidate -> ... -> changed module, following importer -> importee edges.
    nodes: list[RepoPath] = Field(min_length=2)


class ImpactCandidate(StageValue):
    id: Text
    path: RepoPath
    symbol: Text | None = None
    relationship: Literal["changed", "direct", "indirect"]
    changed_component_id: Text
    path_ids: list[Text]
    evidence_ids: list[Text] = Field(default_factory=list)
    explanation: Text | None = None


class ImpactPayload(StageValue):
    snapshot: SnapshotIdentity
    candidates: list[ImpactCandidate]
    paths: list[ImpactPath]


class StageEvidence(StageValue):
    id: Text
    snapshot: SnapshotIdentity
    path: RepoPath
    location: SourceLocation
    symbol: Text | None = None
    excerpt: Text | None = None
    resolution: Literal["unverified", "resolved", "missing", "mismatched"] = "unverified"
    support: Literal["unverified", "supported", "unsupported"] = "unverified"
    verification_reason: Code | None = None

    @model_validator(mode="after")
    def no_implicit_verification(self) -> Self:
        require_snapshot(self.snapshot)
        if self.resolution != "unverified" and self.verification_reason is None:
            raise ValueError("verification_requires_reason")
        if self.support != "unverified" and self.resolution != "resolved":
            raise ValueError("support_requires_resolved_source")
        return self


class EvidencePayload(StageValue):
    items: list[StageEvidence]

    @model_validator(mode="after")
    def identifiers(self) -> Self:
        unique([item.id for item in self.items])
        return self


class InventoryPayload(StageValue):
    snapshot: SnapshotIdentity
    framework: Literal["pytest"]
    test_ids: list[Text]
    completeness: Literal["complete", "partial"]

    @model_validator(mode="after")
    def native_ids_unique(self) -> Self:
        require_snapshot(self.snapshot)
        unique(list(self.test_ids))
        return self


class RetrievalSource(StageValue):
    snapshot: SnapshotIdentity
    index_id: Text
    configuration_id: Text

    @model_validator(mode="after")
    def materialized(self) -> Self:
        require_snapshot(self.snapshot)
        return self


class RetrievalItem(RetrievalSource):
    id: Text
    path: RepoPath
    location: SourceLocation
    content_sha256: Digest
    rank: int = Field(ge=1, strict=True)
    score: float | None = Field(default=None, allow_inf_nan=False)


class RetrievalPayload(StageValue):
    # Even empty retrieval retains queried snapshot/index/config provenance.
    sources: list[RetrievalSource] = Field(min_length=1)
    items: list[RetrievalItem]

    @model_validator(mode="after")
    def identifiers(self) -> Self:
        unique([item.id for item in self.items])
        unique([item.rank for item in self.items])
        keys = [(s.snapshot, s.index_id, s.configuration_id) for s in self.sources]
        unique(list(keys))
        if any(
            (item.snapshot, item.index_id, item.configuration_id) not in keys for item in self.items
        ):
            raise ValueError("retrieval_provenance_mismatch")
        return self


class ReviewItem(StageValue):
    path: RepoPath
    symbol: Text | None = None
    tier: Literal[1, 2, 3]
    reason: Text


class ReviewPayload(StageValue):
    snapshot: SnapshotIdentity
    rule_version: Text
    candidates: list[ReviewItem]

    @model_validator(mode="after")
    def identifiers(self) -> Self:
        require_snapshot(self.snapshot)
        unique([(item.path, item.symbol) for item in self.candidates])
        return self


class AnalysisStages(StageValue):
    snapshots: StageResult[SnapshotPayload]
    changes: StageResult[ChangePayload]
    graph: StageResult[GraphPayload]
    impact: StageResult[ImpactPayload]
    inventory: StageResult[InventoryPayload]
    retrieval: StageResult[RetrievalPayload]
    evidence: StageResult[EvidencePayload]
    review_ordering: StageResult[ReviewPayload]


def validate_artifacts(
    identity: RunIdentity,
    changes: ChangePayload | None,
    graph: GraphPayload | None,
    impact: ImpactPayload | None,
    evidence: EvidencePayload | None,
) -> None:
    snapshots = (identity.base, identity.target)
    if graph is not None and graph.snapshot not in snapshots:
        raise ValueError("foreign_graph_snapshot")
    evidence_ids = {e.id for e in evidence.items} if evidence else set()
    if evidence and any(e.snapshot not in snapshots for e in evidence.items):
        raise ValueError("foreign_evidence_snapshot")
    if impact is None:
        return
    if graph is None or changes is None or impact.snapshot != graph.snapshot:
        raise ValueError("impact_requires_matching_graph_and_changes")
    components = {c.id: c for c in changes.components}
    paths = {p.id: p for p in impact.paths}
    unique([p.id for p in impact.paths])
    unique([(p.changed_component_id, tuple(p.nodes)) for p in impact.paths])
    unique([c.id for c in impact.candidates])
    unique([(c.path, c.symbol, c.changed_component_id) for c in impact.candidates])
    edges = {(e.source, e.target) for e in graph.edges}
    is_base = graph.snapshot == identity.base

    def changed_path(component_id: str) -> str:
        component = components.get(component_id)
        if component is None:
            raise ValueError("unknown_changed_component")
        if (is_base and component.change == "added") or (
            not is_base and component.change == "deleted"
        ):
            raise ValueError("component_absent_from_graph_revision")
        return (component.previous_path or component.path) if is_base else component.path

    for path in impact.paths:
        unique(list(path.nodes))
        if path.nodes[-1] != changed_path(path.changed_component_id):
            raise ValueError("path_does_not_end_at_changed_component")
        if any((a, b) not in edges for a, b in zip(path.nodes, path.nodes[1:], strict=False)):
            raise ValueError("unsupported_impact_path")
    for candidate in impact.candidates:
        origin = changed_path(candidate.changed_component_id)
        unique(list(candidate.path_ids))
        unique(list(candidate.evidence_ids))
        if not set(candidate.evidence_ids) <= evidence_ids:
            raise ValueError("unknown_evidence_reference")
        if candidate.path not in graph.nodes:
            raise ValueError("candidate_not_in_graph")
        if candidate.relationship == "changed":
            if candidate.path != origin or candidate.path_ids:
                raise ValueError("invalid_changed_candidate")
        elif not candidate.path_ids:
            raise ValueError("dependent_requires_path")
        path_lengths = []
        for path_id in candidate.path_ids:
            path = paths.get(path_id)
            if path is None or path.changed_component_id != candidate.changed_component_id:
                raise ValueError("unknown_or_mismatched_path")
            if path.nodes[0] != candidate.path:
                raise ValueError("path_does_not_start_at_candidate")
            path_lengths.append(len(path.nodes))
        if path_lengths:
            expected = "direct" if (candidate.path, origin) in edges else "indirect"
            if candidate.relationship != expected or (
                expected == "direct" and min(path_lengths) != 2
            ):
                raise ValueError("relationship_path_mismatch")


class StageAnalysisReport(StageValue):
    schema_version: Literal["2.0.0"]  # Required discriminator; legacy omission stays v1.
    report_id: Text
    data_kind: Literal["demo", "real"]
    identity: RunIdentity
    analysis_status: StageStatus
    stages: AnalysisStages
    analysis_duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    llm_cost_usd: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def coherent_report(self) -> Self:
        stages = self.stages
        results = [getattr(stages, name) for name in type(stages).model_fields]
        statuses = {result.status for result in results}
        expected = (
            "completed"
            if statuses == {"completed"}
            else "partial"
            if statuses & {"completed", "partial"}
            else "failed"
            if "failed" in statuses
            else "not_run"
            if "not_run" in statuses
            else "not_implemented"
        )
        if self.analysis_status != expected:
            raise ValueError("aggregate_stage_status_mismatch")
        if stages.changes.data is not None:
            require_snapshot(self.identity.base)
            require_snapshot(self.identity.target)
        if stages.snapshots.data and (
            stages.snapshots.data.base != self.identity.base
            or stages.snapshots.data.target != self.identity.target
        ):
            raise ValueError("snapshot_payload_identity_mismatch")
        if stages.changes.data and any(
            f.status != "completed" or f.limitations for f in stages.changes.data.files
        ):
            if stages.changes.status != "partial":
                raise ValueError("partial_file_requires_partial_stage")
        if stages.graph.data and stages.graph.data.unresolved and stages.graph.status != "partial":
            raise ValueError("unresolved_graph_requires_partial_stage")
        if (
            stages.impact.data
            and (stages.changes.status == "partial" or stages.graph.status == "partial")
            and stages.impact.status != "partial"
        ):
            raise ValueError("partial_impact_prerequisite")
        validate_artifacts(
            self.identity,
            stages.changes.data,
            stages.graph.data,
            stages.impact.data,
            stages.evidence.data,
        )
        if stages.inventory.data:
            inventory = stages.inventory.data
            if inventory.snapshot != self.identity.target:
                raise ValueError("inventory_requires_target_snapshot")
            if inventory.completeness == "partial" and stages.inventory.status != "partial":
                raise ValueError("partial_inventory_requires_partial_stage")
        if stages.retrieval.data and any(
            source.snapshot not in (self.identity.base, self.identity.target)
            for source in stages.retrieval.data.sources
        ):
            raise ValueError("foreign_retrieval_snapshot")
        if stages.review_ordering.data:
            if (
                stages.changes.data is None
                or stages.graph.data is None
                or stages.review_ordering.data.snapshot != stages.graph.data.snapshot
            ):
                raise ValueError("review_requires_matching_graph")
            if any(
                c.path not in stages.graph.data.nodes
                for c in stages.review_ordering.data.candidates
            ):
                raise ValueError("review_candidate_not_in_graph")
            if (
                stages.changes.status == "partial" or stages.graph.status == "partial"
            ) and stages.review_ordering.status != "partial":
                raise ValueError("partial_review_prerequisite")
        if (
            stages.evidence.data
            and any(
                item.resolution != "resolved" or item.support != "supported"
                for item in stages.evidence.data.items
            )
            and stages.evidence.status != "partial"
        ):
            raise ValueError("unverified_evidence_requires_partial_stage")
        return self


class EvidenceBundle(StageValue):
    """Atomic domain unit for task 2.05; not a connection or database schema."""

    identity: RunIdentity
    changes: ChangePayload
    graph: GraphPayload
    impact: ImpactPayload
    evidence: EvidencePayload

    @model_validator(mode="after")
    def references(self) -> Self:
        require_snapshot(self.identity.base)
        require_snapshot(self.identity.target)
        validate_artifacts(self.identity, self.changes, self.graph, self.impact, self.evidence)
        return self

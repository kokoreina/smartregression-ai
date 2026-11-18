"""Snapshot-bound explorer facts, bounds, and explicit file denominators."""

from typing import Literal

from pydantic import Field, model_validator

from smartregression.contracts.repository import GitHubCommit as Commit
from smartregression.contracts.repository import WebValue


class GraphEvidence(WebValue):
    id: str
    commit: Commit
    path: str
    kind: Literal["metadata", "source_range"] = "source_range"
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    source_kind: Literal["git", "overlay"] = "git"
    overlay_digest: str | None = None

    @model_validator(mode="after")
    def ordered(self):
        if self.kind == "source_range" and (self.line_start is None or self.line_end is None):
            raise ValueError("source_range_required")
        if self.kind == "metadata" and (self.line_start is not None or self.line_end is not None):
            raise ValueError("metadata_has_no_source_range")
        if (
            self.line_start is not None
            and self.line_end is not None
            and self.line_end < self.line_start
        ):
            raise ValueError("invalid_evidence_range")
        if (self.source_kind == "overlay") != (self.overlay_digest is not None):
            raise ValueError("overlay_evidence_identity_required")
        return self


class ExplorerNode(WebValue):
    id: str
    path: str
    kind: Literal["directory", "file", "function", "class", "method"]
    label: str
    symbol: str | None = None
    evidence: GraphEvidence | None = None


class ExplorerEdge(WebValue):
    id: str
    source: str
    target: str
    source_path: str
    target_path: str
    kind: Literal["contains", "imports", "calls"]
    evidence: GraphEvidence


class UnresolvedRelation(WebValue):
    path: str
    reference: str
    reason: str
    line: int = 1


class ClassifiedReference(WebValue):
    path: str
    reference: str
    category: Literal["builtin", "stdlib"]
    kind: Literal["call", "import"]
    line: int = Field(default=1, ge=1)


class CoverageDiagnostics(WebValue):
    file_groups: dict[str, list[str]]
    unresolved_by_reason: dict[str, int]
    classified_by_kind: dict[str, int]
    excluded_files: list[str] = Field(default_factory=list)


class GraphCoverage(WebValue):
    status: Literal["complete", "partial"]
    analyzed_files: list[str]
    unparsed_files: list[str]
    unsupported_files: list[str]
    diagnostics: CoverageDiagnostics | None = None


class ExplorerGraph(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    repository_id: str
    commit: Commit
    config_digest: str
    overlay_digest: str | None = None
    nodes: list[ExplorerNode]
    edges: list[ExplorerEdge]
    unresolved: list[UnresolvedRelation]
    classified_references: list[ClassifiedReference] = Field(default_factory=list)
    coverage: GraphCoverage

    @model_validator(mode="after")
    def coherent(self):
        from smartregression.core.git.snapshots import validate_snapshot_paths

        nodes = {node.id: node for node in self.nodes}
        if len(nodes) != len(self.nodes) or len({edge.id for edge in self.edges}) != len(
            self.edges
        ):
            raise ValueError("duplicate_graph_identity")
        # A graph explicitly contains directories alongside their children; the
        # snapshot file-set validator correctly rejects that combination as files.
        for path in {node.path for node in self.nodes}:
            validate_snapshot_paths([path])
        if set(self.coverage.analyzed_files) & (
            set(self.coverage.unparsed_files) | set(self.coverage.unsupported_files)
        ):
            raise ValueError("overlapping_graph_coverage")
        evidence = {}
        for item in [
            *(node.evidence for node in self.nodes if node.evidence),
            *(edge.evidence for edge in self.edges),
        ]:
            if item.commit != self.commit or item.id in evidence and evidence[item.id] != item:
                raise ValueError("graph_evidence_mismatch")
            evidence[item.id] = item
            if item.source_kind == "overlay" and item.overlay_digest != self.overlay_digest:
                raise ValueError("overlay_graph_evidence_mismatch")
        for edge in self.edges:
            if edge.source not in nodes or edge.target not in nodes:
                raise ValueError("unknown_graph_endpoint")
            if (
                nodes[edge.source].path != edge.source_path
                or nodes[edge.target].path != edge.target_path
            ):
                raise ValueError("graph_path_mismatch")
            if edge.kind != "contains" and edge.evidence.path != edge.source_path:
                raise ValueError("graph_evidence_path_mismatch")
        return self


class GraphView(WebValue):
    repository_id: str
    commit: Commit
    config_digest: str
    coverage: GraphCoverage
    nodes: list[ExplorerNode]
    edges: list[ExplorerEdge]
    total_nodes: int
    total_edges: int
    truncated: bool


class ImpactSummary(WebValue):
    changed: list[str]
    direct: list[str]
    indirect: list[str]
    denominator: int | None
    percentages: dict[str, float | None]
    counts: dict[str, int]
    unknown_changed_count: int
    paths: dict[str, list[str]]
    paths_truncated: bool = False
    coverage: GraphCoverage
    unresolved_count: int
    interpretation: Literal["potential_static_impact"] = "potential_static_impact"


class Hotspots(WebValue):
    cycles: list[list[str]]
    fan_in: dict[str, int]
    fan_out: dict[str, int]
    cross_module_edges: list[str]


class CallPaths(WebValue):
    paths: list[list[str]]
    nodes: list[ExplorerNode] = Field(default_factory=list, max_length=150)
    unresolved: list[UnresolvedRelation]
    truncated: bool
    interpretation: Literal["static_paths_not_runtime"] = "static_paths_not_runtime"

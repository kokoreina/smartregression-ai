"""Immutable scenarios explicitly distinguish hypotheses from static overlays."""

from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from smartregression.contracts.explorer import (
    ExplorerEdge,
    ExplorerGraph,
    ExplorerNode,
    ImpactSummary,
)
from smartregression.contracts.repository import GitHubCommit as Commit
from smartregression.contracts.repository import NarrativeResult, WebValue
from smartregression.contracts.stages import RepoPath


class GraphDelta(WebValue):
    repository_id: str
    base_commit: Commit
    target_commit: Commit
    config_digest: str
    added_nodes: list[ExplorerNode]
    removed_nodes: list[ExplorerNode]
    retained_node_count: int
    added_edges: list[ExplorerEdge]
    removed_edges: list[ExplorerEdge]
    retained_edge_count: int
    limitations: list[str]
    total_added_nodes: int
    total_removed_nodes: int
    total_added_edges: int
    total_removed_edges: int
    truncated: bool = False


class ScenarioCreate(WebValue):
    baseline: Commit
    path: RepoPath
    title: str = Field(min_length=1, max_length=120)
    mode: Literal["code", "diff", "description"]
    input: str = Field(max_length=262144)
    idempotency_key: str = Field(pattern="^[A-Za-z0-9_-]{8,100}$")

    @model_validator(mode="after")
    def bounds(self):
        if len(self.input.encode("utf-8")) > 262144:
            raise ValueError("overlay_limit")
        if self.mode == "description" and not 1 <= len(self.input) <= 2000:
            raise ValueError("description_limit")
        return self


class Scenario(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    id: UUID
    project_id: UUID
    baseline: Commit
    config_digest: str
    input_digest: str
    title: str
    path: RepoPath
    mode: Literal["code", "diff", "description"]
    input: str
    created_at: AwareDatetime
    analysis_kind: Literal["static_overlay", "hypothesis"]
    graph: ExplorerGraph | None
    delta: GraphDelta | None
    impact: ImpactSummary | None
    narrative: NarrativeResult
    limitations: list[str]

    @model_validator(mode="after")
    def coherent(self):
        if self.mode == "description":
            if self.analysis_kind != "hypothesis" or any(
                x is not None for x in (self.graph, self.delta, self.impact)
            ):
                raise ValueError("hypothesis_has_no_static_facts")
        else:
            if (
                self.analysis_kind != "static_overlay"
                or self.graph is None
                or self.delta is None
                or self.impact is None
            ):
                raise ValueError("overlay_static_result_required")
            if (
                self.graph.commit != self.baseline
                or self.graph.config_digest != self.config_digest
                or self.graph.overlay_digest != self.input_digest
            ):
                raise ValueError("overlay_identity_mismatch")
        return self


class ScenarioPage(WebValue):
    items: list[Scenario]
    next_cursor: str | None = None


class ScenarioComparison(WebValue):
    left: UUID
    right: UUID
    baseline: Commit
    config_digest: str
    added_affected: list[str]
    removed_affected: list[str]
    retained_affected: list[str]
    graph_delta: GraphDelta | None
    comparison_kind: Literal["static_overlays", "hypotheses"] = "static_overlays"
    unresolved_left: int | None
    unresolved_right: int | None
    interpretation: Literal["no_safety_ranking"] = "no_safety_ranking"


class ScenarioView(WebValue):
    id: UUID
    project_id: UUID
    baseline: Commit
    config_digest: str
    input_digest: str
    title: str
    path: RepoPath
    mode: Literal["code", "diff", "description"]
    created_at: AwareDatetime
    analysis_kind: Literal["static_overlay", "hypothesis"]
    impact: ImpactSummary | None
    added_symbols: list[str]
    removed_symbols: list[str]
    added_node_count: int | None
    removed_node_count: int | None
    added_edge_count: int | None
    removed_edge_count: int | None
    limitations: list[str]


class ScenarioViewPage(WebValue):
    items: list[ScenarioView]
    next_cursor: str | None = None


class ScenarioCompareInput(WebValue):
    left: UUID
    right: UUID


class VersionCompareInput(WebValue):
    base: Commit
    target: Commit

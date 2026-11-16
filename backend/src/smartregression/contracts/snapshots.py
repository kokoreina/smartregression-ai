"""Owner-scoped immutable explorer snapshots; source is exposed only by bounded ranges."""

from typing import Literal

from smartregression.contracts.explorer import ExplorerGraph, GraphCoverage
from smartregression.contracts.repository import GitHubCommit as Commit
from smartregression.contracts.repository import RepositoryTree, WebValue


class SnapshotRequest(WebValue):
    commit: Commit


class ExplorerSnapshot(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    graph: ExplorerGraph
    tree: RepositoryTree
    excluded_paths: list[str]


class SourceRange(WebValue):
    commit: Commit
    path: str
    line_start: int
    line_end: int
    content: str
    source_kind: Literal["git", "overlay"] = "git"
    overlay_digest: str | None = None


class SnapshotInfo(WebValue):
    commit: Commit
    config_digest: str
    coverage: GraphCoverage
    total_nodes: int
    total_edges: int
    tree_entries: int
    excluded_count: int

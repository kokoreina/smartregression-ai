"""Owner-scoped bounded graph, source range, call-path and structural queries."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request

from smartregression.api.project_dependencies import product_csrf, verified_owner
from smartregression.application.auth import AuthFailure, User
from smartregression.application.explorer import ExplorerService
from smartregression.contracts.assistance import FeatureQuery, FeatureSearch, ReadingGuide
from smartregression.contracts.explorer import (
    CallPaths,
    ExplorerNode,
    GraphView,
    Hotspots,
    ImpactSummary,
)
from smartregression.contracts.repository import RepositoryTree
from smartregression.contracts.snapshots import SnapshotInfo, SnapshotRequest, SourceRange

Owner = Annotated[User, Depends(verified_owner)]
Commit = Annotated[str, Path(pattern="^[0-9a-f]{40}$")]


def service(request: Request) -> ExplorerService:
    value = getattr(request.app.state, "explorer_service", None)
    if value is None:
        raise AuthFailure("explorer_unavailable", 503)
    return value


Service = Annotated[ExplorerService, Depends(service)]


def explorer_router():
    router = APIRouter(prefix="/api/v1/projects/{project_id}/snapshots", tags=["explorer"])

    @router.post("", response_model=SnapshotInfo, dependencies=[Depends(product_csrf)])
    def materialize(project_id: UUID, body: SnapshotRequest, user: Owner, explorer: Service):
        value = explorer.materialize(user.id, str(project_id), body.commit)
        return SnapshotInfo(
            commit=body.commit,
            config_digest=value.graph.config_digest,
            coverage=value.graph.coverage,
            total_nodes=len(value.graph.nodes),
            total_edges=len(value.graph.edges),
            tree_entries=len(value.tree.entries),
            excluded_count=len(value.excluded_paths),
        )

    @router.get("/{commit}/tree", response_model=RepositoryTree)
    def tree(project_id: UUID, commit: Commit, user: Owner, explorer: Service):
        return explorer.read(user.id, str(project_id), commit)[0].tree

    @router.get("/{commit}/graph", response_model=GraphView)
    def graph(
        project_id: UUID,
        commit: Commit,
        user: Owner,
        explorer: Service,
        focus: str | None = Query(None, max_length=2048),
        limit: int = Query(150, ge=1, le=150),
        direction: Literal["both", "dependencies", "dependents"] = "both",
        depth: int = Query(2, ge=0, le=10),
    ):
        return explorer.graph(user.id, str(project_id), commit, focus, limit, direction, depth)

    @router.get("/{commit}/nodes", response_model=list[ExplorerNode])
    def nodes(
        project_id: UUID,
        commit: Commit,
        user: Owner,
        explorer: Service,
        offset: int = Query(0, ge=0, le=10000),
        limit: int = Query(100, ge=1, le=100),
        search: str = Query("", max_length=120),
    ):
        value = explorer.read(user.id, str(project_id), commit)[0].graph
        return [
            node
            for node in value.nodes
            if search.casefold() in (node.path + " " + (node.symbol or "")).casefold()
        ][offset : offset + limit]

    @router.get("/{commit}/source", response_model=SourceRange)
    def source(
        project_id: UUID,
        commit: Commit,
        user: Owner,
        explorer: Service,
        path: str = Query(max_length=2048),
        start: int = Query(1, ge=1),
        end: int = Query(100, ge=1),
    ):
        return explorer.source(user.id, str(project_id), commit, path, start, end)

    @router.get("/{commit}/impact", response_model=ImpactSummary)
    def impact(
        project_id: UUID,
        commit: Commit,
        user: Owner,
        explorer: Service,
        path: str = Query(max_length=2048),
    ):
        return explorer.impact(user.id, str(project_id), commit, {path})

    @router.get("/{commit}/hotspots", response_model=Hotspots)
    def hotspots(project_id: UUID, commit: Commit, user: Owner, explorer: Service):
        return explorer.hotspots(user.id, str(project_id), commit)

    @router.get("/{commit}/calls", response_model=CallPaths)
    def calls(
        project_id: UUID,
        commit: Commit,
        user: Owner,
        explorer: Service,
        node: str = Query(max_length=64),
        depth: int = Query(10, ge=1, le=10),
        limit: int = Query(20, ge=1, le=20),
    ):
        return explorer.calls(user.id, str(project_id), commit, node, depth, limit)

    @router.get("/{commit}/reading-guide", response_model=ReadingGuide)
    def guide(project_id: UUID, commit: Commit, user: Owner, explorer: Service):
        return explorer.reading_guide(user.id, str(project_id), commit)

    @router.post(
        "/{commit}/search", response_model=FeatureSearch, dependencies=[Depends(product_csrf)]
    )
    def search(
        project_id: UUID, commit: Commit, body: FeatureQuery, user: Owner, explorer: Service
    ):
        return explorer.search(user.id, str(project_id), commit, body.query, body.top_k)

    return router

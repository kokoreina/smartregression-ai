"""Immutable scenario and comparison APIs; source inputs are never executed."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from smartregression.api.project_dependencies import product_csrf, verified_owner
from smartregression.application.auth import AuthFailure, User
from smartregression.application.scenarios import ScenarioService, scenario_view
from smartregression.contracts.explorer import GraphView
from smartregression.contracts.scenarios import (
    GraphDelta,
    ScenarioCompareInput,
    ScenarioComparison,
    ScenarioCreate,
    ScenarioView,
    ScenarioViewPage,
    VersionCompareInput,
)
from smartregression.contracts.snapshots import SourceRange
from smartregression.core.explorer.graph import neighborhood
from smartregression.core.explorer.scenarios import overlay

Owner = Annotated[User, Depends(verified_owner)]


def service(request: Request) -> ScenarioService:
    value = getattr(request.app.state, "scenario_service", None)
    if value is None:
        raise AuthFailure("scenarios_unavailable", 503)
    return value


Service = Annotated[ScenarioService, Depends(service)]


def bounded(delta: GraphDelta) -> GraphDelta:
    return delta.model_copy(
        update={
            "added_nodes": delta.added_nodes[:150],
            "removed_nodes": delta.removed_nodes[:150],
            "added_edges": delta.added_edges[:1000],
            "removed_edges": delta.removed_edges[:1000],
            "truncated": len(delta.added_nodes) > 150
            or len(delta.removed_nodes) > 150
            or len(delta.added_edges) > 1000
            or len(delta.removed_edges) > 1000,
        }
    )


def scenario_router():
    router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["scenarios"])

    @router.post(
        "/scenarios",
        response_model=ScenarioView,
        status_code=201,
        dependencies=[Depends(product_csrf)],
    )
    def create(project_id: UUID, body: ScenarioCreate, user: Owner, scenarios: Service):
        return scenario_view(scenarios.create(user.id, str(project_id), body))

    @router.get("/scenarios", response_model=ScenarioViewPage)
    def listing(
        project_id: UUID,
        user: Owner,
        scenarios: Service,
        cursor: str | None = Query(None, max_length=256),
        limit: int = Query(25, ge=1, le=100),
    ):
        return scenarios.list(user.id, str(project_id), cursor, limit)

    @router.get("/scenarios/{scenario_id}", response_model=ScenarioView)
    def detail(project_id: UUID, scenario_id: UUID, user: Owner, scenarios: Service):
        return scenario_view(scenarios.store.get(user.id, str(project_id), str(scenario_id)))

    @router.get("/scenarios/{scenario_id}/graph", response_model=GraphView)
    def graph(project_id: UUID, scenario_id: UUID, user: Owner, scenarios: Service):
        value = scenarios.store.get(user.id, str(project_id), str(scenario_id))
        if value.graph is None:
            raise AuthFailure("hypothesis_has_no_static_graph", 409)
        return neighborhood(value.graph, focus_path=value.path)

    @router.get("/scenarios/{scenario_id}/source", response_model=SourceRange)
    def source(
        project_id: UUID,
        scenario_id: UUID,
        user: Owner,
        scenarios: Service,
        start: int = Query(1, ge=1),
        end: int = Query(100, ge=1),
    ):
        value = scenarios.store.get(user.id, str(project_id), str(scenario_id))
        if value.mode == "description":
            raise AuthFailure("hypothesis_has_no_source", 409)
        _, sources = scenarios.explorer.read(user.id, str(project_id), value.baseline)
        changed = overlay(
            sources,
            value.path,
            **({"content": value.input} if value.mode == "code" else {"patch": value.input}),
        )
        lines = changed[value.path].splitlines()
        if end < start or end - start >= 200 or start > len(lines):
            raise AuthFailure("source_range_limit", 422)
        content = "\n".join(lines[start - 1 : end])
        if len(content.encode()) > 20000:
            raise AuthFailure("source_range_limit", 422)
        return SourceRange(
            commit=value.baseline,
            path=value.path,
            line_start=start,
            line_end=min(end, len(lines)),
            content=content,
            source_kind="overlay",
            overlay_digest=value.input_digest,
        )

    @router.post(
        "/scenario-comparisons",
        response_model=ScenarioComparison,
        dependencies=[Depends(product_csrf)],
    )
    def compare(project_id: UUID, body: ScenarioCompareInput, user: Owner, scenarios: Service):
        result = scenarios.compare(user.id, str(project_id), str(body.left), str(body.right))
        if result.graph_delta:
            result.graph_delta = bounded(result.graph_delta)
        return result

    @router.post(
        "/graph-comparisons", response_model=GraphDelta, dependencies=[Depends(product_csrf)]
    )
    def versions(project_id: UUID, body: VersionCompareInput, user: Owner, scenarios: Service):
        return bounded(scenarios.versions(user.id, str(project_id), body.base, body.target))

    return router

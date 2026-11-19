"""Durable static analysis transport. Background work never executes repository code."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request

from smartregression.api.project_dependencies import product_csrf, verified_owner
from smartregression.application.auth import AuthFailure, User
from smartregression.application.web_runs import WebRunService
from smartregression.contracts.web_runs import RunCreate, RunPage, RunStatus, SavedRunReport, WebRun

Owner = Annotated[User, Depends(verified_owner)]


def service(request: Request) -> WebRunService:
    value = getattr(request.app.state, "web_run_service", None)
    if value is None:
        raise AuthFailure("analysis_unavailable", 503)
    return value


Service = Annotated[WebRunService, Depends(service)]


def web_run_router():
    router = APIRouter(prefix="/api/v1/projects/{project_id}/runs", tags=["runs"])

    @router.post("", response_model=WebRun, status_code=202, dependencies=[Depends(product_csrf)])
    def create(
        project_id: UUID, body: RunCreate, user: Owner, runs: Service, tasks: BackgroundTasks
    ):
        result, created = runs.create(user.id, str(project_id), body)
        if created:
            tasks.add_task(runs.execute, user.id, str(project_id), str(result.id))
        return result

    @router.get("", response_model=RunPage)
    def listing(
        project_id: UUID,
        user: Owner,
        runs: Service,
        cursor: str | None = Query(None, max_length=256),
        limit: int = Query(25, ge=1, le=100),
        status: RunStatus | None = None,
    ):
        return runs.store.list(user.id, str(project_id), cursor, limit, status=status)

    @router.get("/{run_id}", response_model=WebRun)
    def detail(project_id: UUID, run_id: UUID, user: Owner, runs: Service):
        return runs.store.get(user.id, str(project_id), str(run_id))

    @router.get("/{run_id}/report", response_model=SavedRunReport)
    def report(project_id: UUID, run_id: UUID, user: Owner, runs: Service):
        return runs.store.report(user.id, str(project_id), str(run_id))

    return router

"""Owner-scoped frozen dashboard views and downloads; writes require CSRF."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from smartregression.api.project_dependencies import product_csrf, verified_owner
from smartregression.application.auth import AuthFailure, User
from smartregression.application.web_reporting import WebReportingService
from smartregression.contracts.web_reporting import Dashboard, DashboardQuery, UsagePage
from smartregression.contracts.web_runs import RunPage

Owner = Annotated[User, Depends(verified_owner)]


def service(request: Request) -> WebReportingService:
    value = getattr(request.app.state, "reporting_service", None)
    if value is None:
        raise AuthFailure("reporting_unavailable", 503)
    return value


Service = Annotated[WebReportingService, Depends(service)]


def reporting_router():
    router = APIRouter(prefix="/api/v1/reporting", tags=["reporting"])

    @router.post("/views", response_model=Dashboard, dependencies=[Depends(product_csrf)])
    def create(body: DashboardQuery, user: Owner, reports: Service):
        return reports.create(user.id, body)

    @router.get("/views/{view_id}", response_model=Dashboard)
    def read(view_id: UUID, user: Owner, reports: Service):
        return reports.read(user.id, str(view_id))

    @router.get("/views/{view_id}/runs", response_model=RunPage)
    def listing(
        view_id: UUID,
        user: Owner,
        reports: Service,
        offset: int = Query(0, ge=0, le=10000),
        limit: int = Query(25, ge=1, le=100),
    ):
        return reports.page(user.id, str(view_id), offset, limit)

    @router.post("/views/{view_id}/csv", dependencies=[Depends(product_csrf)])
    def download(view_id: UUID, user: Owner, reports: Service):
        return Response(
            content=reports.csv(user.id, str(view_id)),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="smartregression-runs.csv"',
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @router.get("/views/{view_id}/usage", response_model=UsagePage)
    def usage(
        view_id: UUID,
        user: Owner,
        reports: Service,
        offset: int = Query(0, ge=0, le=10000),
        limit: int = Query(25, ge=1, le=100),
    ):
        return reports.usage(user.id, str(view_id), offset, limit)

    return router

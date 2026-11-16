"""Download generation is recorded, not successful client receipt."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response

from smartregression.api.project_dependencies import product_csrf, verified_owner
from smartregression.application.auth import AuthFailure, User
from smartregression.application.web_exports import WebExportService
from smartregression.contracts.web_exports import DurableRunExport, ScenarioExport

Owner = Annotated[User, Depends(verified_owner)]


def service(request: Request):
    state = request.app.state
    values = [
        getattr(state, k, None) for k in ["web_run_service", "scenario_service", "web_ai_service"]
    ]
    if any(value is None for value in values):
        raise AuthFailure("reporting_unavailable", 503)
    return WebExportService(*values)


Service = Annotated[WebExportService, Depends(service)]


def export_router():
    router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["export"])

    def download(value, kind):
        return Response(
            content=value.model_dump_json(),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="smartregression-{kind}.json"',
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @router.post(
        "/runs/{run_id}/export",
        response_model=DurableRunExport,
        dependencies=[Depends(product_csrf)],
    )
    def run(project_id: UUID, run_id: UUID, user: Owner, exports: Service):
        return download(exports.run(user.id, str(project_id), str(run_id)), "run")

    @router.post(
        "/scenarios/{scenario_id}/export",
        response_model=ScenarioExport,
        dependencies=[Depends(product_csrf)],
    )
    def scenario(project_id: UUID, scenario_id: UUID, user: Owner, exports: Service):
        return download(exports.scenario(user.id, str(project_id), str(scenario_id)), "scenario")

    return router

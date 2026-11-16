"""Explicit consent-bound AI requests and owner-scoped quota visibility."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from smartregression.api.project_dependencies import product_csrf, verified_owner
from smartregression.application.auth import AuthFailure, User
from smartregression.application.web_ai import WebAiService
from smartregression.contracts.ai_requests import AiJob, AiQuota, AssistanceAiRequest
from smartregression.contracts.web_runs import AiRequest

Owner = Annotated[User, Depends(verified_owner)]


def service(request: Request) -> WebAiService:
    value = getattr(request.app.state, "web_ai_service", None)
    if value is None:
        raise AuthFailure("ai_unavailable", 503)
    return value


Service = Annotated[WebAiService, Depends(service)]


def web_ai_router():
    router = APIRouter(prefix="/api/v1", tags=["AI"])

    @router.get("/usage", response_model=AiQuota)
    def usage(user: Owner, ai: Service):
        return ai.store.quota(user.id)

    @router.post(
        "/projects/{project_id}/runs/{run_id}/ai",
        response_model=AiJob,
        status_code=202,
        dependencies=[Depends(product_csrf)],
    )
    def request_ai(
        project_id: UUID,
        run_id: UUID,
        body: AiRequest,
        user: Owner,
        ai: Service,
        tasks: BackgroundTasks,
    ):
        result, created, batch, campaign = ai.create(user.id, str(project_id), str(run_id), body)
        if created:
            tasks.add_task(
                ai.execute,
                user.id,
                str(project_id),
                str(run_id),
                str(result.id),
                batch,
                campaign,
                body.question,
            )
        return result

    @router.get("/projects/{project_id}/runs/{run_id}/ai/{request_id}", response_model=AiJob)
    def detail(project_id: UUID, run_id: UUID, request_id: UUID, user: Owner, ai: Service):
        return ai.store.get(user.id, str(project_id), str(run_id), str(request_id))

    def scoped(ai, request):
        from smartregression.application.assistance_ai import AssistanceAiService

        explorer = getattr(request.app.state, "explorer_service", None)
        scenarios = getattr(request.app.state, "scenario_service", None)
        if explorer is None or scenarios is None:
            raise AuthFailure("ai_unavailable", 503)
        return AssistanceAiService(ai.store, explorer, scenarios, ai.explain)

    @router.post(
        "/projects/{project_id}/assistance/ai",
        response_model=AiJob,
        status_code=202,
        dependencies=[Depends(product_csrf)],
    )
    def assistance(
        project_id: UUID,
        body: AssistanceAiRequest,
        user: Owner,
        ai: Service,
        request: Request,
        tasks: BackgroundTasks,
    ):
        service = scoped(ai, request)
        result, created, batch, campaign, context = service.create(user.id, str(project_id), body)
        if created:
            tasks.add_task(service.execute, user.id, str(result.id), batch, campaign, context)
        return result

    @router.get("/projects/{project_id}/assistance/ai", response_model=list[AiJob])
    def assistance_list(project_id: UUID, user: Owner, ai: Service, commit: str):
        import re

        if not re.fullmatch("[0-9a-f]{40}", commit):
            raise AuthFailure("invalid_commit", 422)
        return ai.store.scoped_list(user.id, str(project_id), commit)

    @router.get("/projects/{project_id}/assistance/ai/{request_id}", response_model=AiJob)
    def assistance_get(project_id: UUID, request_id: UUID, user: Owner, ai: Service):
        return ai.store.scoped_get(user.id, str(project_id), str(request_id))

    return router

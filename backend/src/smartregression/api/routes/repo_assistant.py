"""Repository assistant API; user requests require a verified owner and write CSRF."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response

from smartregression.api.project_dependencies import product_csrf, verified_owner
from smartregression.application.auth import AuthFailure, User
from smartregression.application.repo_assistant import RepositoryAssistantService
from smartregression.contracts.repo_assistant import (
    AssistantMessage,
    AssistantReply,
    AssistantThread,
    ChangeNotification,
    MessageCreate,
    RepositoryWatch,
    ThreadCreate,
    WatchInput,
    WebhookReceipt,
)

Owner = Annotated[User, Depends(verified_owner)]


def service(request: Request) -> RepositoryAssistantService:
    value = getattr(request.app.state, "repo_assistant_service", None)
    if value is None:
        raise AuthFailure("assistant_unavailable", 503)
    return value


Service = Annotated[RepositoryAssistantService, Depends(service)]


def repo_assistant_router():
    router = APIRouter(
        prefix="/api/v1/projects/{project_id}/assistant", tags=["repository assistant"]
    )

    @router.post("/overview", response_model=AssistantReply, dependencies=[Depends(product_csrf)])
    def overview(
        project_id: UUID,
        user: Owner,
        assistant: Service,
        commit: str | None = Query(None, pattern="^[0-9a-f]{40}$"),
    ):
        return assistant.overview(user.id, str(project_id), commit)

    @router.get("/threads", response_model=list[AssistantThread])
    def threads(project_id: UUID, user: Owner, assistant: Service):
        return assistant.store.threads(user.id, str(project_id))

    @router.post("/threads", response_model=AssistantThread, dependencies=[Depends(product_csrf)])
    def create_thread(project_id: UUID, body: ThreadCreate, user: Owner, assistant: Service):
        return assistant.create_thread(user.id, str(project_id), body)

    @router.delete("/threads/{thread_id}", status_code=204, dependencies=[Depends(product_csrf)])
    def delete_thread(project_id: UUID, thread_id: UUID, user: Owner, assistant: Service):
        assistant.store.delete_thread(user.id, str(project_id), str(thread_id))
        return Response(status_code=204)

    @router.get("/threads/{thread_id}/messages", response_model=list[AssistantMessage])
    def messages(project_id: UUID, thread_id: UUID, user: Owner, assistant: Service):
        return assistant.messages(user.id, str(project_id), str(thread_id))

    @router.post(
        "/threads/{thread_id}/preview",
        response_model=AssistantReply,
        dependencies=[Depends(product_csrf)],
    )
    def preview(
        project_id: UUID, thread_id: UUID, body: MessageCreate, user: Owner, assistant: Service
    ):
        return assistant.preview(user.id, str(project_id), str(thread_id), body)

    @router.post(
        "/threads/{thread_id}/messages",
        response_model=AssistantMessage,
        dependencies=[Depends(product_csrf)],
    )
    def send(
        project_id: UUID,
        thread_id: UUID,
        body: MessageCreate,
        user: Owner,
        assistant: Service,
        tasks: BackgroundTasks,
    ):
        message, execution = assistant.send(user.id, str(project_id), str(thread_id), body)
        if execution:
            tasks.add_task(assistant.execute_ai, *execution)
        return message

    @router.get("/watch", response_model=RepositoryWatch | None)
    def watch(project_id: UUID, user: Owner, assistant: Service):
        return assistant.store.watch(user.id, str(project_id))

    @router.put("/watch", response_model=RepositoryWatch, dependencies=[Depends(product_csrf)])
    def save_watch(project_id: UUID, body: WatchInput, user: Owner, assistant: Service):
        return assistant.save_watch(user.id, str(project_id), body)

    @router.post(
        "/check",
        status_code=202,
        response_model=RepositoryWatch,
        dependencies=[Depends(product_csrf)],
    )
    def check(project_id: UUID, user: Owner, assistant: Service, tasks: BackgroundTasks):
        result = assistant.store.schedule(user.id, str(project_id))
        tasks.add_task(assistant.process_once, user.id, str(project_id))
        return result

    @router.get("/notifications", response_model=list[ChangeNotification])
    def notifications(project_id: UUID, user: Owner, assistant: Service):
        return assistant.store.notifications(user.id, str(project_id))

    @router.post(
        "/notifications/{notification_id}/read",
        status_code=204,
        dependencies=[Depends(product_csrf)],
    )
    def mark_read(project_id: UUID, notification_id: UUID, user: Owner, assistant: Service):
        assistant.store.read_notification(user.id, str(project_id), str(notification_id))
        return Response(status_code=204)

    return router


def github_webhook_router():
    router = APIRouter(tags=["GitHub integration"])

    @router.post("/api/v1/github/webhook", response_model=WebhookReceipt)
    async def webhook(request: Request, assistant: Service):
        from starlette.concurrency import run_in_threadpool

        from smartregression.adapters.github_webhooks import receive_delivery
        from smartregression.auth_config import web_environment

        return await run_in_threadpool(
            receive_delivery,
            assistant.store,
            await request.body(),
            request.headers,
            web_environment().get("SMARTREGRESSION_GITHUB_WEBHOOK_SECRET", ""),
        )

    return router

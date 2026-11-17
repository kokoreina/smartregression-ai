"""API composition root. Demo data is a static frontend fixture, not an API result."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from smartregression.api.routes.health import router
from smartregression.application.auth import AuthFailure, AuthService
from smartregression.application.explorer import ExplorerService
from smartregression.application.notes import NoteService
from smartregression.application.projects import ProjectService
from smartregression.application.repository_analysis import RepositoryService
from smartregression.application.run_store import RunStorageError
from smartregression.application.scenarios import ScenarioService
from smartregression.application.web_ai import WebAiService
from smartregression.application.web_runs import WebRunService
from smartregression.auth_config import AuthSettings
from smartregression.contracts.auth import AuthErrorResponse, WebCapabilities
from smartregression.contracts.models import ErrorResponse


def create_app(
    *,
    repository_service: RepositoryService | None = None,
    auth_service: AuthService | None = None,
    auth_settings: AuthSettings | None = None,
    project_service: ProjectService | None = None,
    web_run_service: WebRunService | None = None,
    web_ai_service: WebAiService | None = None,
    explorer_service: ExplorerService | None = None,
    note_service: NoteService | None = None,
    scenario_service: ScenarioService | None = None,
    reporting_service=None,
    mode: str | None = None,
) -> FastAPI:
    from smartregression.api.routes.auth import auth_router
    from smartregression.api.routes.explorer import explorer_router
    from smartregression.api.routes.notes import note_router
    from smartregression.api.routes.projects import project_router
    from smartregression.api.routes.repositories import repository_router
    from smartregression.api.routes.scenarios import scenario_router
    from smartregression.api.routes.web_ai import web_ai_router
    from smartregression.api.routes.web_exports import export_router
    from smartregression.api.routes.web_reporting import reporting_router
    from smartregression.api.routes.web_runs import web_run_router
    from smartregression.composition import repository_web_service

    selected_mode = mode or os.environ.get("SMARTREGRESSION_WEB_MODE", "local-demo")
    if selected_mode not in {"local-demo", "product"}:
        raise ValueError("invalid_web_mode")

    @asynccontextmanager
    async def lifespan(app):
        if auth_service is not None:
            yield
            return
        from contextlib import ExitStack

        from smartregression.composition import account_service

        with ExitStack() as stack:
            configured = account_service(stack, required=selected_mode == "product")
            if configured:
                app.state.auth_service, app.state.auth_settings = configured
                from smartregression.composition import (
                    durable_run_service,
                    personal_project_service,
                    product_ai_service,
                    product_explorer_service,
                    product_note_service,
                    product_scenario_service,
                )

                app.state.project_service = personal_project_service(app.state.auth_service)
                app.state.web_run_service = durable_run_service(stack, app.state.auth_service)
                app.state.web_ai_service = product_ai_service(
                    app.state.auth_service, app.state.web_run_service
                )
                app.state.explorer_service = product_explorer_service(app.state.auth_service)
                app.state.note_service = product_note_service(app.state.auth_service)
                app.state.scenario_service = product_scenario_service(
                    app.state.auth_service, app.state.explorer_service
                )
                from smartregression.composition import product_reporting_service

                app.state.reporting_service = product_reporting_service(app.state.auth_service)
            yield

    app = FastAPI(title="SmartRegression AI", version="0.1.0", lifespan=lifespan)
    app.state.auth_service, app.state.auth_settings = auth_service, auth_settings
    app.state.project_service = project_service
    app.state.web_run_service = web_run_service
    app.state.web_ai_service = web_ai_service
    app.state.explorer_service = explorer_service
    app.state.note_service = note_service
    app.state.scenario_service = scenario_service
    app.state.reporting_service = reporting_service
    app.include_router(router)
    app.include_router(auth_router())
    app.include_router(project_router())
    app.include_router(web_run_router())
    app.include_router(web_ai_router())
    app.include_router(explorer_router())
    app.include_router(note_router())
    app.include_router(scenario_router())
    app.include_router(reporting_router())
    app.include_router(export_router())
    if selected_mode == "local-demo":
        app.include_router(repository_router(repository_service or repository_web_service()))

    @app.get("/api/v1/capabilities", response_model=WebCapabilities)
    def capabilities():
        return WebCapabilities(local_demo=selected_mode == "local-demo")

    @app.middleware("http")
    async def bounded_request(request: Request, call_next):
        if selected_mode == "product" and request.url.path in {
            "/repositories/inspect",
            "/repositories/tree",
            "/repository-analyses",
            "/api/repositories/inspect",
            "/api/repositories/tree",
            "/api/repository-analyses",
        }:
            return JSONResponse(status_code=404, content={"code": "not_found"})
        auth_path = request.url.path.startswith("/api/v1/")
        if request.method in {"POST", "PATCH", "PUT"} and (
            auth_path
            or request.url.path
            in {
                "/repositories/inspect",
                "/repositories/tree",
                "/repository-analyses",
            }
        ):
            if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
                return JSONResponse(
                    status_code=415,
                    content={"code": "json_required", "message": "Yêu cầu phải là JSON."},
                )
            size = 0
            parts = []
            async for part in request.stream():
                size += len(part)
                body_limit = (
                    8192 if request.url.path.startswith("/api/v1/auth/") or not auth_path else 65536
                )
                if "scenarios" in request.url.path.split("/"):
                    body_limit = 2 * 1024 * 1024
                if size > body_limit:
                    return JSONResponse(
                        status_code=413,
                        content={"code": "request_limit", "message": "Yêu cầu quá lớn."},
                    )
                parts.append(part)
            request._body = b"".join(parts)
        response = await call_next(request)
        if request.url.path.startswith("/api/v1/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        if request.url.path.startswith("/api/v1/auth/"):
            return JSONResponse(
                status_code=422,
                content=AuthErrorResponse(
                    code="invalid_request",
                    message="Thông tin chưa hợp lệ. Kiểm tra email, mật khẩu và biểu mẫu.",
                ).model_dump(),
            )
        return JSONResponse(
            status_code=422,
            content={
                "code": "invalid_request",
                "message": "URL GitHub, commit hoặc xác nhận gửi metadata chưa hợp lệ.",
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        error = ErrorResponse(code=f"http_{exc.status_code}", message=str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=error.model_dump())

    @app.exception_handler(AuthFailure)
    async def auth_error(request: Request, exc: AuthFailure):
        return JSONResponse(
            status_code=exc.status,
            content=AuthErrorResponse(
                code=exc.code, message="Không thể hoàn tất yêu cầu tài khoản."
            ).model_dump(),
            headers={"Retry-After": str(exc.retry_after)} if exc.retry_after else None,
        )

    @app.exception_handler(RunStorageError)
    async def storage_error(request: Request, exc: RunStorageError):
        return JSONResponse(
            status_code=503,
            content=AuthErrorResponse(
                code="account_storage_unavailable",
                message="Dịch vụ tài khoản tạm thời không khả dụng.",
            ).model_dump(),
        )

    return app


app = create_app()

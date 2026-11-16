"""Thin same-origin account transport; no credentials in errors or access URLs."""

from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Request, Response

from smartregression.adapters.auth_security import CsrfSigner
from smartregression.application.auth import AuthFailure, AuthService
from smartregression.auth_config import AuthSettings
from smartregression.contracts.auth import (
    AuthErrorResponse,
    AuthMessage,
    CsrfToken,
    CurrentUser,
    EmailInput,
    Login,
    PasswordChange,
    PasswordReset,
    ProfileUpdate,
    Registration,
    TokenInput,
)

NEUTRAL = "Đã tiếp nhận yêu cầu. Nếu thông tin phù hợp, hãy kiểm tra hộp thư và thư rác."


def auth_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/auth",
        tags=["account"],
        responses={
            status: {"model": AuthErrorResponse} for status in (400, 401, 403, 422, 429, 503)
        },
    )

    def configuration(request: Request) -> AuthSettings:
        value = getattr(request.app.state, "auth_settings", None)
        if value is None:
            raise AuthFailure("authentication_unavailable", 503)
        host = request.url.hostname
        expected = urlsplit(value.frontend_origin).hostname
        if host != expected and not (value.local_http and host in {"localhost", "127.0.0.1"}):
            raise AuthFailure("invalid_host", 403)
        return value

    def service(request: Request) -> AuthService:
        value = getattr(request.app.state, "auth_service", None)
        if value is None:
            raise AuthFailure("authentication_unavailable", 503)
        return value

    def session(request: Request, settings: AuthSettings) -> str:
        return request.cookies.get(settings.session_cookie, "")

    def csrf(request: Request, settings: Annotated[AuthSettings, Depends(configuration)]):
        if request.headers.get("origin") != settings.frontend_origin:
            raise AuthFailure("invalid_origin", 403)
        if not CsrfSigner(settings.csrf_secret).valid(
            request.cookies.get(settings.csrf_cookie, ""),
            request.headers.get("x-csrf-token", ""),
            session(request, settings),
        ):
            raise AuthFailure("csrf_invalid", 403)

    def cookie(response: Response, name: str, value: str, age: int, settings: AuthSettings):
        response.set_cookie(
            name,
            value,
            max_age=age,
            httponly=True,
            secure=not settings.local_http,
            samesite="lax",
            path="/",
        )

    def rotate(response: Response, settings: AuthSettings, session_value: str):
        value = CsrfSigner(settings.csrf_secret).issue(session_value)
        cookie(response, settings.csrf_cookie, value, CsrfSigner.ttl, settings)

    def ip(request: Request) -> str:
        # Uvicorn must run with --no-proxy-headers until a trusted proxy is configured.
        return request.client.host if request.client else "unknown"

    @router.get("/csrf", response_model=CsrfToken)
    def get_csrf(
        request: Request,
        response: Response,
        settings: Annotated[AuthSettings, Depends(configuration)],
    ):
        signer = CsrfSigner(settings.csrf_secret)
        current = request.cookies.get(settings.csrf_cookie, "")
        sid = session(request, settings)
        value = current if signer.valid(current, current, sid) else signer.issue(sid)
        cookie(response, settings.csrf_cookie, value, signer.ttl, settings)
        return CsrfToken(token=value)

    @router.post(
        "/register", status_code=202, response_model=AuthMessage, dependencies=[Depends(csrf)]
    )
    def register(
        body: Registration, request: Request, auth: Annotated[AuthService, Depends(service)]
    ):
        auth.register(
            str(body.email), body.password.get_secret_value(), body.display_name, ip(request)
        )
        return AuthMessage(message=NEUTRAL)

    @router.post("/login", response_model=CurrentUser, dependencies=[Depends(csrf)])
    def login(
        body: Login,
        request: Request,
        response: Response,
        auth: Annotated[AuthService, Depends(service)],
        settings: Annotated[AuthSettings, Depends(configuration)],
    ):
        user, raw = auth.login(
            str(body.email),
            body.password.get_secret_value(),
            ip(request),
            session(request, settings),
        )
        cookie(response, settings.session_cookie, raw, 7 * 86400, settings)
        rotate(response, settings, raw)
        return user.public()

    @router.post("/logout", response_model=AuthMessage, dependencies=[Depends(csrf)])
    def logout(
        request: Request,
        response: Response,
        auth: Annotated[AuthService, Depends(service)],
        settings: Annotated[AuthSettings, Depends(configuration)],
    ):
        auth.logout(session(request, settings))
        response.delete_cookie(
            settings.session_cookie,
            path="/",
            httponly=True,
            secure=not settings.local_http,
            samesite="lax",
        )
        rotate(response, settings, "")
        return AuthMessage(message="Đã đăng xuất.")

    @router.get("/me", response_model=CurrentUser)
    def me(
        request: Request,
        auth: Annotated[AuthService, Depends(service)],
        settings: Annotated[AuthSettings, Depends(configuration)],
    ):
        return auth.current(session(request, settings)).public()

    @router.patch("/me", response_model=CurrentUser, dependencies=[Depends(csrf)])
    def update_me(
        body: ProfileUpdate,
        request: Request,
        auth: Annotated[AuthService, Depends(service)],
        settings: Annotated[AuthSettings, Depends(configuration)],
    ):
        return auth.profile(session(request, settings), body.display_name).public()

    @router.post("/verify-email", response_model=AuthMessage, dependencies=[Depends(csrf)])
    def verify(body: TokenInput, auth: Annotated[AuthService, Depends(service)]):
        auth.verify_email(body.token.get_secret_value())
        return AuthMessage(message="Email đã được xác thực. Bạn có thể đăng nhập.")

    @router.post(
        "/resend-verification",
        status_code=202,
        response_model=AuthMessage,
        dependencies=[Depends(csrf)],
    )
    def resend(body: EmailInput, request: Request, auth: Annotated[AuthService, Depends(service)]):
        auth.request_token(str(body.email), "verify", ip(request))
        return AuthMessage(message=NEUTRAL)

    @router.post(
        "/forgot-password",
        status_code=202,
        response_model=AuthMessage,
        dependencies=[Depends(csrf)],
    )
    def forgot(body: EmailInput, request: Request, auth: Annotated[AuthService, Depends(service)]):
        auth.request_token(str(body.email), "reset", ip(request))
        return AuthMessage(message=NEUTRAL)

    def clear_session(response: Response, settings: AuthSettings):
        response.delete_cookie(
            settings.session_cookie,
            path="/",
            httponly=True,
            secure=not settings.local_http,
            samesite="lax",
        )
        rotate(response, settings, "")

    @router.post("/reset-password", response_model=AuthMessage, dependencies=[Depends(csrf)])
    def reset(
        body: PasswordReset,
        response: Response,
        auth: Annotated[AuthService, Depends(service)],
        settings: Annotated[AuthSettings, Depends(configuration)],
    ):
        auth.reset(body.token.get_secret_value(), body.password.get_secret_value())
        clear_session(response, settings)
        return AuthMessage(message="Mật khẩu đã đổi. Hãy đăng nhập lại.")

    @router.post("/change-password", response_model=AuthMessage, dependencies=[Depends(csrf)])
    def change(
        body: PasswordChange,
        request: Request,
        response: Response,
        auth: Annotated[AuthService, Depends(service)],
        settings: Annotated[AuthSettings, Depends(configuration)],
    ):
        auth.change_password(
            session(request, settings),
            body.current_password.get_secret_value(),
            body.password.get_secret_value(),
            ip(request),
        )
        clear_session(response, settings)
        return AuthMessage(message="Mật khẩu đã đổi. Tất cả phiên cũ đã được thu hồi.")

    return router

"""Shared same-origin owner boundary for every product data route."""

from urllib.parse import urlsplit

from fastapi import Request

from smartregression.adapters.auth_security import CsrfSigner
from smartregression.application.auth import AuthFailure, User


def verified_owner(request: Request) -> User:
    settings = getattr(request.app.state, "auth_settings", None)
    auth = getattr(request.app.state, "auth_service", None)
    if settings is None or auth is None:
        raise AuthFailure("authentication_unavailable", 503)
    expected = urlsplit(settings.frontend_origin).hostname
    if request.url.hostname != expected and not (
        settings.local_http and request.url.hostname in {"localhost", "127.0.0.1"}
    ):
        raise AuthFailure("invalid_host", 403)
    return auth.current(request.cookies.get(settings.session_cookie, ""), verified=True)


def product_csrf(request: Request) -> None:
    settings = getattr(request.app.state, "auth_settings", None)
    if settings is None:
        raise AuthFailure("authentication_unavailable", 503)
    if request.headers.get("origin") != settings.frontend_origin:
        raise AuthFailure("invalid_origin", 403)
    if not CsrfSigner(settings.csrf_secret).valid(
        request.cookies.get(settings.csrf_cookie, ""),
        request.headers.get("x-csrf-token", ""),
        request.cookies.get(settings.session_cookie, ""),
    ):
        raise AuthFailure("csrf_invalid", 403)

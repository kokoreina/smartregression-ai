"""Project contract and authenticated API boundary regressions."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smartregression.api.main import create_app
from smartregression.application.auth import AuthFailure, User
from smartregression.auth_config import AuthSettings
from smartregression.contracts.projects import ProjectCreate, ProjectUpdate


def test_project_contract_rejects_owner_and_invalid_repository():
    with pytest.raises(ValidationError):
        ProjectCreate(title="Demo", repository_url="https://github.com/a/b", owner_id=str(uuid4()))
    for url in ("file:///etc/passwd", "https://github.com.evil/a/b", "http://github.com/a/b"):
        with pytest.raises(ValidationError):
            ProjectCreate(title="Demo", repository_url=url)
    value = ProjectCreate(title=" Demo ", repository_url="https://github.com/a/b.git")
    assert value.title == "Demo" and value.repository_url == "https://github.com/a/b"
    with pytest.raises(ValidationError):
        ProjectUpdate(title="Demo", version=0)


class Accounts:
    def current(self, raw, *, verified=False):
        if raw != "verified-session":
            raise AuthFailure("invalid_session", 401)
        return User(str(uuid4()), "test@example.com", "Test", verified=True, enabled=True)


@pytest.mark.parametrize("code", ["github_rate_limit", "github_timeout", "repository_limit"])
def test_product_errors_preserve_allowlisted_recovery_code_without_raw_details(code):
    from smartregression.application.projects import ProjectService

    def unavailable(url):
        raise ValueError(code)

    service = ProjectService(None, unavailable)
    with pytest.raises(AuthFailure, match=code):
        service.create(
            "owner", ProjectCreate(title="Example", repository_url="https://github.com/a/b")
        )


def test_product_errors_hide_unrecognized_upstream_details():
    from smartregression.application.projects import ProjectService

    def unavailable(url):
        raise ValueError("private upstream detail must not escape")

    service = ProjectService(None, unavailable)
    with pytest.raises(AuthFailure, match="repository_lookup_failed"):
        service.create(
            "owner", ProjectCreate(title="Example", repository_url="https://github.com/a/b")
        )


def test_projects_require_session_and_csrf_before_service():
    settings = AuthSettings("http://127.0.0.1:5173", b"x" * 32, True)
    with TestClient(
        create_app(auth_service=Accounts(), auth_settings=settings),
        base_url="http://127.0.0.1:5173",
    ) as client:
        assert client.get("/api/v1/projects").status_code == 401
        client.cookies.set(settings.session_cookie, "verified-session")
        response = client.post(
            "/api/v1/projects",
            json={"title": "Demo", "repository_url": "https://github.com/a/b"},
            headers={"Origin": settings.frontend_origin},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "csrf_invalid"

"""Product transport matrix: real auth/CSRF, recording data boundary, no network/DB.

The recording boundary proves session-owner propagation, not SQL row isolation.
Real PostgreSQL isolation checks are mapped separately in the task handoff.
"""

import hashlib
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from smartregression.adapters.auth_security import CsrfSigner
from smartregression.api.main import create_app
from smartregression.application.auth import AuthFailure, AuthService, User
from smartregression.auth_config import AuthSettings

PROJECT = "10000000-0000-4000-8000-000000000001"
OBJECT = "20000000-0000-4000-8000-000000000002"
OWNER_A = "30000000-0000-4000-8000-000000000003"
OWNER_B = "40000000-0000-4000-8000-000000000004"
COMMIT = "a" * 40
PREFIX = "/api/v1/projects"
P = PREFIX + "/{project_id}"
R = P + "/runs"
S = P + "/snapshots"
V = "/api/v1/reporting/views"
WRITES = {"POST", "PATCH", "PUT", "DELETE"}


@dataclass(frozen=True)
class AccessCase:
    method: str
    path: str
    body_kind: str | None = None

    @property
    def key(self):
        return f"{self.method} {self.path}"

    @property
    def url(self):
        return self.path.format(
            project_id=PROJECT,
            run_id=OBJECT,
            request_id=OBJECT,
            scenario_id=OBJECT,
            note_id=OBJECT,
            view_id=OBJECT,
            commit=COMMIT,
        )

    def body(self):
        bodies = {
            "project": {"title": "Synthetic", "repository_url": "https://github.com/owner/repo"},
            "update": {"title": "Synthetic", "version": 1},
            "version": {"version": 1},
            "run": {"base": COMMIT, "target": "b" * 40, "idempotency_key": "matrix-run"},
            "ai": {"idempotency_key": "matrix-ai", "allow_metadata_egress": True},
            "assistance": {
                "commit": COMMIT,
                "action": "file",
                "path": "main.py",
                "idempotency_key": "matrix-assistance",
                "allow_metadata_egress": True,
            },
            "snapshot": {"commit": COMMIT},
            "search": {"query": "payment"},
            "note": {"commit": COMMIT, "path": "main.py", "title": "Synthetic note"},
            "state": {"commit": COMMIT, "version": 0},
            "scenario": {
                "baseline": COMMIT,
                "path": "main.py",
                "title": "Synthetic overlay",
                "mode": "code",
                "input": "value = 1\n",
                "idempotency_key": "matrix-scenario",
            },
            "compare": {"left": OBJECT, "right": PROJECT},
            "versions": {"base": COMMIT, "target": "b" * 40},
            "dashboard": {},
        }
        return bodies[self.body_kind] if self.body_kind else {}


# Explicit inventory: a newly added data endpoint requires a reviewed matrix case.
CASES = tuple(
    AccessCase(*row)
    for row in [
        ("GET", PREFIX),
        ("POST", PREFIX, "project"),
        ("GET", P),
        ("PATCH", P, "update"),
        ("POST", P + "/archive", "version"),
        ("POST", P + "/restore", "version"),
        ("GET", P + "/activity"),
        ("GET", P + "/repository"),
        ("GET", P + "/tree"),
        ("POST", R, "run"),
        ("GET", R),
        ("GET", R + "/{run_id}"),
        ("GET", R + "/{run_id}/report"),
        ("GET", "/api/v1/usage"),
        ("POST", R + "/{run_id}/ai", "ai"),
        ("GET", R + "/{run_id}/ai/{request_id}"),
        ("POST", P + "/assistance/ai", "assistance"),
        ("GET", P + "/assistance/ai"),
        ("GET", P + "/assistance/ai/{request_id}"),
        ("POST", S, "snapshot"),
        *[
            ("GET", S + "/{commit}/" + tail)
            for tail in (
                "tree",
                "graph",
                "nodes",
                "source",
                "impact",
                "hotspots",
                "calls",
                "reading-guide",
            )
        ],
        ("POST", S + "/{commit}/search", "search"),
        ("POST", P + "/notes", "note"),
        ("PATCH", P + "/notes/{note_id}", "update"),
        ("GET", P + "/notes"),
        ("GET", P + "/view-state"),
        ("PUT", P + "/view-state", "state"),
        ("POST", P + "/scenarios", "scenario"),
        ("GET", P + "/scenarios"),
        ("GET", P + "/scenarios/{scenario_id}"),
        ("GET", P + "/scenarios/{scenario_id}/graph"),
        ("GET", P + "/scenarios/{scenario_id}/source"),
        ("POST", P + "/scenario-comparisons", "compare"),
        ("POST", P + "/graph-comparisons", "versions"),
        ("POST", R + "/{run_id}/export"),
        ("POST", P + "/scenarios/{scenario_id}/export"),
        ("POST", V, "dashboard"),
        ("GET", V + "/{view_id}"),
        ("GET", V + "/{view_id}/runs"),
        ("POST", V + "/{view_id}/csv"),
        ("GET", V + "/{view_id}/usage"),
    ]
)
WRITE_CASES = tuple(c for c in CASES if c.method in WRITES)
ACCOUNT_AND_PUBLIC_OPERATIONS = {
    ("GET", "/health"),
    ("GET", "/api/v1/capabilities"),
    ("GET", "/api/v1/auth/csrf"),
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/auth/me"),
    ("PATCH", "/api/v1/auth/me"),
    ("POST", "/api/v1/auth/verify-email"),
    ("POST", "/api/v1/auth/resend-verification"),
    ("POST", "/api/v1/auth/forgot-password"),
    ("POST", "/api/v1/auth/reset-password"),
    ("POST", "/api/v1/auth/change-password"),
}


def digest(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


class SessionStore:
    """Synthetic session records exercise the actual AuthService.current logic."""

    def __init__(self):
        future = datetime.now(UTC) + timedelta(hours=1)
        past = datetime.now(UTC) - timedelta(hours=1)
        self.records = {
            digest(token): (
                User(owner, "synthetic@example.com", "Synthetic", "unused", **flags),
                end,
            )
            for token, owner, flags, end in [
                ("session-a", OWNER_A, {"verified": True}, future),
                ("session-b", OWNER_B, {"verified": True}, future),
                ("unverified", OWNER_A, {"verified": False}, future),
                ("disabled", OWNER_A, {"verified": True, "enabled": False}, future),
                ("expired", OWNER_A, {"verified": True}, past),
            ]
        }

    @contextmanager
    def transaction(self):
        yield self

    def session_user(self, identity, now):
        record = self.records.get(identity)
        return record[0] if record and record[1] > now else None


class DataBoundary:
    """Stop at first service/store access, recording the effective owner only."""

    def __init__(self):
        self._events = []

    @property
    def store(self):
        return self

    def __getattr__(self, method):
        def record(owner, *args, **kwargs):
            self._events.append((method, owner))
            raise AuthFailure("matrix_data_boundary", 409)

        return record


@pytest.fixture(scope="module")
def matrix_client():
    settings = AuthSettings("http://127.0.0.1:5173", b"matrix-test-only-" * 2, True)
    boundary = DataBoundary()
    auth = AuthService(SessionStore(), None, None, digest)
    app = create_app(
        auth_service=auth,
        auth_settings=settings,
        mode="product",
        project_service=boundary,
        web_run_service=boundary,
        web_ai_service=boundary,
        explorer_service=boundary,
        scenario_service=boundary,
        note_service=boundary,
        reporting_service=boundary,
    )
    with TestClient(app, base_url=settings.frontend_origin) as client:
        yield client, settings, boundary


def send(matrix_client, case, token, *, protection="valid", body=None, extra_headers=None):
    client, settings, boundary = matrix_client
    boundary._events.clear()
    client.cookies.clear()
    if token:
        client.cookies.set(settings.session_cookie, token)
    csrf = CsrfSigner(settings.csrf_secret).issue(token)
    client.cookies.set(settings.csrf_cookie, csrf)
    headers = {"Origin": settings.frontend_origin, "X-CSRF-Token": csrf}
    if protection == "missing":
        headers.pop("X-CSRF-Token")
    elif protection == "other-session":
        other = CsrfSigner(settings.csrf_secret).issue("different-session")
        client.cookies.set(settings.csrf_cookie, other)
        headers["X-CSRF-Token"] = other
    elif protection == "other-origin":
        headers["Origin"] = "https://other.example"
    headers.update(extra_headers or {})
    return client.request(
        case.method,
        case.url,
        headers=headers,
        params={"commit": COMMIT, "path": "main.py", "node": "synthetic-node", "owner_id": OWNER_A},
        **({"json": case.body() if body is None else body} if case.method in WRITES else {}),
    )


def assert_product_inventory(matrix_client):
    client, _, _ = matrix_client
    expected = {
        (method.upper(), path)
        for path, operations in client.app.openapi()["paths"].items()
        for method in operations
        if method.upper() in {"GET", *WRITES}
    }
    actual = {(c.method, c.path) for c in CASES}
    assert len(actual) == len(CASES)
    assert ACCOUNT_AND_PUBLIC_OPERATIONS <= expected
    assert actual.isdisjoint(ACCOUNT_AND_PUBLIC_OPERATIONS)
    assert actual == expected - ACCOUNT_AND_PUBLIC_OPERATIONS
    assert not any(
        part in {"members", "roles", "assignments", "invites"}
        for _, path in expected
        for part in path.split("/")
    )


def test_matrix_covers_every_product_data_endpoint(matrix_client):
    assert_product_inventory(matrix_client)


def test_new_data_namespace_requires_a_matrix_case(matrix_client):
    app = matrix_client[0].app
    original_routes = list(app.router.routes)
    try:

        @app.get("/api/v1/exports")
        def unreviewed_export():
            return {}

        app.openapi_schema = None
        with pytest.raises(AssertionError):
            assert_product_inventory(matrix_client)
    finally:
        app.router.routes[:] = original_routes
        app.openapi_schema = None


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
@pytest.mark.parametrize(
    "token,status,code",
    [
        ("", 401, "authentication_required"),
        ("invalid", 401, "authentication_required"),
        ("expired", 401, "authentication_required"),
        ("disabled", 401, "authentication_required"),
        ("unverified", 403, "email_verification_required"),
    ],
)
def test_restricted_sessions_stop_before_data_access(matrix_client, case, token, status, code):
    response = send(matrix_client, case, token)
    assert (response.status_code, response.json()["code"]) == (status, code)
    assert matrix_client[2]._events == []


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
@pytest.mark.parametrize("token,owner", [("session-a", OWNER_A), ("session-b", OWNER_B)])
def test_verified_routes_forward_session_owner_despite_spoof_headers(
    matrix_client, case, token, owner
):
    response = send(
        matrix_client, case, token, extra_headers={"X-Owner-ID": OWNER_A, "X-User-ID": OWNER_A}
    )
    assert (response.status_code, response.json()["code"]) == (409, "matrix_data_boundary")
    assert len(matrix_client[2]._events) == 1
    assert matrix_client[2]._events[0][1] == owner


@pytest.mark.parametrize("case", WRITE_CASES, ids=lambda c: c.key)
@pytest.mark.parametrize(
    "protection,code",
    [
        ("missing", "csrf_invalid"),
        ("other-session", "csrf_invalid"),
        ("other-origin", "invalid_origin"),
    ],
)
def test_mutations_and_exports_require_session_bound_csrf(matrix_client, case, protection, code):
    response = send(matrix_client, case, "session-a", protection=protection)
    assert (response.status_code, response.json()["code"]) == (403, code)
    assert matrix_client[2]._events == []


@pytest.mark.parametrize("case", [c for c in CASES if c.body_kind], ids=lambda c: c.key)
def test_input_contract_rejects_client_owner_fields(matrix_client, case):
    response = send(matrix_client, case, "session-b", body=case.body() | {"owner_id": OWNER_A})
    assert (response.status_code, response.json()["code"]) == (422, "invalid_request")
    assert matrix_client[2]._events == []

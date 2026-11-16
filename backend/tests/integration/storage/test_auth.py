"""Real PostgreSQL account transactions and same-origin HTTP boundaries."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier, Event
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from smartregression.adapters.auth_security import PasswordHasher, token_hash
from smartregression.adapters.storage.auth_store import PostgresAuthStore
from smartregression.api.main import create_app
from smartregression.application.auth import AuthFailure, AuthService, MailDeliveryError
from smartregression.auth_config import AuthSettings

PASSWORD = "a sufficiently long password"
NEW_PASSWORD = "another sufficiently long password"


class Mailbox:
    def __init__(self):
        self.messages = []
        self.fail = False

    def send(self, email, purpose, token):
        if self.fail:
            raise MailDeliveryError()
        self.messages.append((email, purpose, token))


@pytest.fixture
def accounts(migrated):
    owner, runtime, _ = migrated
    now = [datetime.now(UTC)]
    mailbox = Mailbox()
    service = AuthService(
        PostgresAuthStore(runtime), PasswordHasher(), mailbox, token_hash, lambda: now[0]
    )
    return service, mailbox, now, owner, runtime


def register(accounts):
    service, mailbox, *_ = accounts
    email = uuid4().hex + "@example.com"
    service.register(email, PASSWORD, "Huy", uuid4().hex)
    return email, mailbox.messages[-1][2]


def login(accounts, email):
    return accounts[0].login(email, PASSWORD, uuid4().hex)


def test_register_session_verify_profile_and_hash_only_storage(accounts):
    service, mailbox, _, owner, _ = accounts
    email, token = register(accounts)
    user, raw = login(accounts, email)
    assert not service.current(raw).verified
    with pytest.raises(AuthFailure, match="email_verification_required"):
        service.current(raw, verified=True)
    service.verify_email(token)
    assert service.current(raw, verified=True).verified
    assert service.profile(raw, "Huy Leader").display_name == "Huy Leader"
    with owner.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM smartregression.web_users WHERE id=:id"), {"id": user.id}
        ).first()
        assert row.password_hash.startswith("$argon2id$") and PASSWORD not in row.password_hash
        assert conn.execute(
            text("SELECT digest FROM smartregression.web_sessions WHERE user_id=:id"),
            {"id": user.id},
        ).scalar() == token_hash(raw)
        assert conn.execute(
            text("SELECT digest FROM smartregression.web_account_tokens WHERE user_id=:id"),
            {"id": user.id},
        ).scalar() == token_hash(token)
    service.logout(raw)
    with pytest.raises(AuthFailure, match="authentication_required"):
        service.current(raw)


def test_login_rotation_expiry_and_wrong_credentials(accounts):
    service, _, now, *_ = accounts
    email, _ = register(accounts)
    with pytest.raises(AuthFailure, match="invalid_credentials"):
        service.login(email, "wrong", uuid4().hex)
    _, old = login(accounts, email)
    _, new = service.login(email, PASSWORD, uuid4().hex, old)
    with pytest.raises(AuthFailure):
        service.current(old)
    assert service.current(new).email == email
    now[0] += timedelta(days=7, seconds=1)
    with pytest.raises(AuthFailure):
        service.current(new)


def test_reset_revokes_all_sessions_and_all_tokens(accounts):
    service, mailbox, *_ = accounts
    email, verify = register(accounts)
    service.verify_email(verify)
    _, first = login(accounts, email)
    _, second = login(accounts, email)
    service.request_token(email, "reset", uuid4().hex)
    token = mailbox.messages[-1][2]
    with pytest.raises(AuthFailure):
        service.verify_email(token)
    service.reset(token, NEW_PASSWORD)
    for raw in [first, second]:
        with pytest.raises(AuthFailure):
            service.current(raw)
    with pytest.raises(AuthFailure):
        service.reset(token, NEW_PASSWORD)
    assert service.login(email, NEW_PASSWORD, uuid4().hex)[0].verified


def test_expired_token_resend_and_failed_delivery_do_not_verify(accounts):
    service, mailbox, now, *_ = accounts
    email, token = register(accounts)
    now[0] += timedelta(hours=25)
    with pytest.raises(AuthFailure):
        service.verify_email(token)
    service.request_token(email, "verify", uuid4().hex)
    replacement = mailbox.messages[-1][2]
    with pytest.raises(AuthFailure):
        service.verify_email(token)
    mailbox.fail = True
    service.request_token(email, "verify", uuid4().hex)
    with pytest.raises(AuthFailure):
        service.verify_email(replacement)
    assert not login(accounts, email)[0].verified


def test_change_and_disable_revoke_sessions(accounts):
    service, *_ = accounts
    email, token = register(accounts)
    service.verify_email(token)
    user, first = login(accounts, email)
    _, second = login(accounts, email)
    with pytest.raises(AuthFailure):
        service.change_password(first, "wrong", NEW_PASSWORD, uuid4().hex)
    service.change_password(first, PASSWORD, NEW_PASSWORD, uuid4().hex)
    for raw in [first, second]:
        with pytest.raises(AuthFailure):
            service.current(raw)
    _, new = service.login(email, NEW_PASSWORD, uuid4().hex)
    service.disable(user.id)
    with pytest.raises(AuthFailure):
        service.current(new)
    with pytest.raises(AuthFailure):
        service.login(email, NEW_PASSWORD, uuid4().hex)


def test_concurrent_token_consume_has_one_winner(accounts):
    service, *_ = accounts
    _, token = register(accounts)
    barrier = Barrier(2)

    def consume():
        barrier.wait()
        try:
            service.verify_email(token)
            return True
        except AuthFailure:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: consume(), range(2))) == [False, True]


def test_concurrent_registration_has_one_account_and_one_mail(accounts):
    service, mailbox, _, owner, _ = accounts
    email = uuid4().hex + "@example.com"
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: service.register(email, PASSWORD, "Huy", uuid4().hex), range(2)))
    with owner.connect() as conn:
        assert (
            conn.execute(
                text("SELECT count(*) FROM smartregression.web_users WHERE email=:email"),
                {"email": email},
            ).scalar()
            == 1
        )
    assert len(mailbox.messages) == 1


def test_atomic_rate_limit_across_workers(accounts):
    service, *_ = accounts
    ip = uuid4().hex
    barrier = Barrier(2)
    # Each worker has a different store instance but shares PostgreSQL.
    other = AuthService(PostgresAuthStore(accounts[4]), service.hasher, accounts[1], token_hash)

    def attempt(s):
        barrier.wait()
        allowed = 0
        for _ in range(4):
            try:
                s._limits("login", ip, uuid4().hex + "@example.com")
                allowed += 1
            except AuthFailure as error:
                assert error.status == 429 and error.retry_after > 0
        return allowed

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(attempt, [service, other])) == 5


def client_for(accounts, *, secure=False):
    origin = "https://testserver" if secure else "http://127.0.0.1:5173"
    settings = AuthSettings(origin, b"x" * 32, not secure)
    app = create_app(auth_service=accounts[0], auth_settings=settings, mode="product")
    return TestClient(app, base_url=origin), origin


def csrf(client, origin):
    token = client.get("/api/v1/auth/csrf").json()["token"]
    return {"Origin": origin, "X-CSRF-Token": token}


def test_http_csrf_origin_session_and_cross_account_profile(accounts):
    email, _ = register(accounts)
    client, origin = client_for(accounts)
    with client:
        assert client.get("/api/v1/auth/me").status_code == 401
        payload = {"email": email, "password": PASSWORD}
        assert client.post("/api/v1/auth/login", json=payload).status_code == 403
        headers = csrf(client, origin)
        assert (
            client.post(
                "/api/v1/auth/login",
                json=payload,
                headers={**headers, "Origin": "https://attacker.test"},
            ).status_code
            == 403
        )
        response = client.post("/api/v1/auth/login", json=payload, headers=headers)
        assert response.status_code == 200 and "password" not in response.text
        assert client.get("/api/v1/auth/me").headers["cache-control"] == "no-store"
        assert (
            client.patch(
                "/api/v1/auth/me",
                headers=csrf(client, origin),
                json={"display_name": "Attacker", "id": str(uuid4())},
            ).status_code
            == 422
        )
        old = client.cookies.get("sr_dev_session")
        assert (
            client.post("/api/v1/auth/logout", json={}, headers=csrf(client, origin)).status_code
            == 200
        )
        client.cookies.set("sr_dev_session", old)
        assert client.get("/api/v1/auth/me").status_code == 401


def test_https_flags_legacy_routes_disabled_and_safe_errors(accounts):
    email, _ = register(accounts)
    client, origin = client_for(accounts, secure=True)
    with client:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": PASSWORD},
            headers=csrf(client, origin),
        )
        flags = response.headers.get_list("set-cookie")
        assert all("HttpOnly" in c and "Secure" in c and "SameSite=lax" in c for c in flags)
        assert any("__Host-sr_session" in c for c in flags)
        assert all("Domain=" not in c for c in flags)
        assert client.post("/repository-analyses", json={}).status_code == 404
        response = client.post(
            "/api/v1/auth/reset-password",
            headers=csrf(client, origin),
            json={"token": "synthetic-secret", "password": "secret"},
        )
        assert response.status_code == 422 and "synthetic-secret" not in response.text


def test_runtime_cannot_drop_tables(accounts):
    with pytest.raises(DBAPIError), accounts[4].begin() as connection:
        connection.execute(text("ALTER TABLE smartregression.web_users ADD COLUMN forbidden TEXT"))


@pytest.mark.parametrize("operation", ["reset", "disable"])
def test_login_in_flight_cannot_escape_password_or_disable_revocation(accounts, operation):
    service, mailbox, *_ = accounts
    email, token = register(accounts)
    service.verify_email(token)
    user, _ = login(accounts, email)
    service.request_token(email, "reset", uuid4().hex)
    reset_token = mailbox.messages[-1][2]
    ready, resume = Event(), Event()

    class PausedHasher:
        def hash(self, value):
            return service.hasher.hash(value)

        def verify(self, value, digest):
            result = service.hasher.verify(value, digest)
            ready.set()
            assert resume.wait(timeout=10)
            return result

    concurrent = AuthService(service.store, PausedHasher(), mailbox, token_hash)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(concurrent.login, email, PASSWORD, uuid4().hex)
        assert ready.wait(timeout=10)
        try:
            if operation == "reset":
                service.reset(reset_token, NEW_PASSWORD)
            else:
                service.disable(user.id)
        finally:
            resume.set()
        with pytest.raises(AuthFailure, match="invalid_credentials"):
            future.result(timeout=10)


def test_reset_token_expires_after_one_hour(accounts):
    service, mailbox, now, *_ = accounts
    email, _ = register(accounts)
    service.request_token(email, "reset", uuid4().hex)
    token = mailbox.messages[-1][2]
    now[0] += timedelta(hours=1, seconds=1)
    with pytest.raises(AuthFailure, match="invalid_or_expired_token"):
        service.reset(token, NEW_PASSWORD)


def test_resend_throttle_returns_retry_after_and_old_csrf_is_rejected(accounts):
    email, _ = register(accounts)
    client, origin = client_for(accounts)
    with client:
        first = csrf(client, origin)
        assert (
            client.post(
                "/api/v1/auth/login", headers=first, json={"email": email, "password": PASSWORD}
            ).status_code
            == 200
        )
        assert (
            client.patch("/api/v1/auth/me", headers=first, json={"display_name": "Huy"}).status_code
            == 403
        )
        for _ in range(3):
            assert (
                client.post(
                    "/api/v1/auth/resend-verification",
                    headers=csrf(client, origin),
                    json={"email": email},
                ).status_code
                == 202
            )
        response = client.post(
            "/api/v1/auth/resend-verification", headers=csrf(client, origin), json={"email": email}
        )
        assert response.status_code == 429
        assert int(response.headers["retry-after"]) > 0

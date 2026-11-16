"""Account use cases. Transactions own mutations; mail happens after commit."""

import logging
import secrets
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

from smartregression.contracts.auth import CurrentUser


class AuthFailure(Exception):
    def __init__(self, code: str, status: int = 400, retry_after: int | None = None):
        self.code, self.status, self.retry_after = code, status, retry_after
        super().__init__(code)


@dataclass(frozen=True)
class User:
    id: str
    email: str
    display_name: str
    password_hash: str = field(repr=False)
    verified: bool = False
    enabled: bool = True

    def public(self) -> CurrentUser:
        return CurrentUser(
            id=self.id, email=self.email, display_name=self.display_name, verified=self.verified
        )


class AuthTransaction(Protocol):
    def user_by_email(self, email: str) -> User | None: ...
    def user_by_id(self, user_id: str) -> User | None: ...
    def insert_user(self, user: User) -> bool: ...
    def session_user(self, digest: str, now: datetime) -> User | None: ...
    def create_session(self, digest: str, user_id: str, expires: datetime) -> None: ...
    def revoke_session(self, digest: str) -> None: ...
    def revoke_all(self, user_id: str) -> None: ...
    def create_token(self, digest: str, user_id: str, purpose: str, expires: datetime) -> None: ...
    def token_user(self, digest: str, purpose: str, now: datetime) -> str | None: ...
    def consume_token(self, digest: str, purpose: str, now: datetime) -> bool: ...
    def set_verified(self, user_id: str) -> None: ...
    def set_password(self, user_id: str, password_hash: str) -> None: ...
    def set_name(self, user_id: str, name: str) -> None: ...
    def disable(self, user_id: str) -> None: ...
    def take_limit(self, key: str, start: datetime, limit: int) -> bool: ...


class AuthStore(Protocol):
    def transaction(self) -> AbstractContextManager[AuthTransaction]: ...


class Hashing(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, digest: str | None) -> bool: ...


class MailDeliveryError(Exception):
    def __init__(self, code: str = "delivery_failed"):
        self.code = (
            code
            if code
            in {
                "authentication_failed",
                "connection_failed",
                "recipient_rejected",
                "delivery_failed",
            }
            else "delivery_failed"
        )
        super().__init__(self.code)


class AccountMailer(Protocol):
    def send(self, email: str, purpose: str, token: str) -> None: ...


class AuthService:
    def __init__(
        self,
        store: AuthStore,
        hasher: Hashing,
        mailer: AccountMailer,
        digest: Callable[[str], str],
        clock: Callable[[], datetime] | None = None,
    ):
        self.store, self.hasher, self.mailer, self.digest = store, hasher, mailer, digest
        self.clock = clock or (lambda: datetime.now(UTC))

    def _limits(self, action: str, ip: str, email: str = "") -> None:
        seconds, maximum = (
            (60, 5) if action == "login" else (3600, 5 if action == "register" else 3)
        )
        now = self.clock()
        start = datetime.fromtimestamp(int(now.timestamp()) // seconds * seconds, UTC)
        keys = [f"{action}:ip:{ip}"]
        if email and action != "register":
            keys.append(f"{action}:email:{email}")
        with self.store.transaction() as tx:
            for key in sorted(keys):
                if not tx.take_limit(self.digest(key), start, maximum):
                    wait = max(1, seconds - int((now - start).total_seconds()))
                    raise AuthFailure("rate_limited", 429, wait)

    def _send(self, email: str, purpose: str, token: str) -> None:
        try:
            self.mailer.send(email, purpose, token)
        except MailDeliveryError as error:
            # No recipient, token, SMTP response or secret in shared diagnostics.
            logging.getLogger(__name__).warning("account_mail_%s", error.code)

    def _token(self, tx: AuthTransaction, user: User, purpose: str) -> str:
        token = secrets.token_urlsafe(32)
        expiry = self.clock() + timedelta(hours=24 if purpose == "verify" else 1)
        tx.create_token(self.digest(token), user.id, purpose, expiry)
        return token

    def register(self, email: str, password: str, name: str, ip: str) -> None:
        self._limits("register", ip)
        user = User(str(uuid4()), email, name, self.hasher.hash(password))
        with self.store.transaction() as tx:
            if not tx.insert_user(user):
                return
            token = self._token(tx, user, "verify")
        self._send(email, "verify", token)

    def login(self, email: str, password: str, ip: str, previous: str = "") -> tuple[User, str]:
        self._limits("login", ip, email)
        with self.store.transaction() as tx:
            candidate = tx.user_by_email(email)
        valid = self.hasher.verify(password, candidate.password_hash if candidate else None)
        if not candidate or not candidate.enabled or not valid:
            raise AuthFailure("invalid_credentials", 401)
        # Separate revocation transaction avoids locking accounts in opposite order
        # when two browsers switch from A to B and B to A concurrently.
        if previous:
            self.logout(previous)
        session = secrets.token_urlsafe(32)
        with self.store.transaction() as tx:
            user = tx.user_by_id(candidate.id)
            if not user or not user.enabled or user.password_hash != candidate.password_hash:
                raise AuthFailure("invalid_credentials", 401)
            tx.create_session(self.digest(session), user.id, self.clock() + timedelta(days=7))
        return user, session

    def current(self, session: str, *, verified: bool = False) -> User:
        with self.store.transaction() as tx:
            return self._current(tx, session, verified=verified)

    def _current(self, tx: AuthTransaction, session: str, *, verified: bool = False) -> User:
        user = tx.session_user(self.digest(session), self.clock()) if session else None
        if not user or not user.enabled:
            raise AuthFailure("authentication_required", 401)
        if verified and not user.verified:
            raise AuthFailure("email_verification_required", 403)
        return user

    def logout(self, session: str) -> None:
        with self.store.transaction() as tx:
            tx.revoke_session(self.digest(session))

    def profile(self, session: str, name: str) -> User:
        with self.store.transaction() as tx:
            user = self._current(tx, session)
            tx.set_name(user.id, name)
            result = tx.user_by_id(user.id)
            assert result is not None
            return result

    def request_token(self, email: str, purpose: str, ip: str) -> None:
        self._limits("resend" if purpose == "verify" else "forgot", ip, email)
        with self.store.transaction() as tx:
            user = tx.user_by_email(email)
            if not user or not user.enabled or (purpose == "verify" and user.verified):
                return
            # Lock account before issuing; serialize with disable/reset.
            user = tx.user_by_id(user.id)
            if not user or not user.enabled or (purpose == "verify" and user.verified):
                return
            token = self._token(tx, user, purpose)
        self._send(email, purpose, token)

    def _consume(self, tx: AuthTransaction, token: str, purpose: str) -> User:
        digest, now = self.digest(token), self.clock()
        user_id = tx.token_user(digest, purpose, now)
        user = tx.user_by_id(user_id) if user_id else None
        if not user or not user.enabled or not tx.consume_token(digest, purpose, now):
            raise AuthFailure("invalid_or_expired_token")
        return user

    def verify_email(self, token: str) -> None:
        with self.store.transaction() as tx:
            user = self._consume(tx, token, "verify")
            tx.set_verified(user.id)

    def reset(self, token: str, password: str) -> None:
        password_hash = self.hasher.hash(password)
        with self.store.transaction() as tx:
            user = self._consume(tx, token, "reset")
            tx.set_password(user.id, password_hash)
            tx.revoke_all(user.id)

    def change_password(self, session: str, current: str, password: str, ip: str) -> None:
        user = self.current(session, verified=True)
        self._limits("login", ip, user.email)
        if not self.hasher.verify(current, user.password_hash):
            raise AuthFailure("invalid_credentials", 401)
        password_hash = self.hasher.hash(password)
        with self.store.transaction() as tx:
            locked = self._current(tx, session, verified=True)
            if locked.password_hash != user.password_hash:
                raise AuthFailure("authentication_required", 401)
            tx.set_password(user.id, password_hash)
            tx.revoke_all(user.id)

    def disable(self, user_id: str) -> None:
        with self.store.transaction() as tx:
            if not tx.user_by_id(user_id):
                raise AuthFailure("account_not_found", 404)
            tx.disable(user_id)
            tx.revoke_all(user_id)

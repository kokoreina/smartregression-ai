"""Standard Argon2id and a signed, session-bound double-submit CSRF token."""

import hashlib
import hmac
import secrets
import time

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError


class PasswordHasher:
    def __init__(self):
        self._hasher = PasswordHash.recommended()
        self._dummy = self._hasher.hash(secrets.token_urlsafe(32))

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, digest: str | None) -> bool:
        try:
            result = self._hasher.verify(password, digest or self._dummy)
            return bool(digest) and result
        except UnknownHashError, ValueError:
            return False


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class CsrfSigner:
    ttl = 3600

    def __init__(self, secret: bytes):
        if len(secret) < 32:
            raise ValueError("csrf_configuration_required")
        self._secret = secret

    def _signature(self, value: str, session: str) -> str:
        payload = f"{value}:{token_hash(session)}".encode()
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()

    def issue(self, session: str, *, now: int | None = None) -> str:
        timestamp = int(time.time()) if now is None else now
        value = f"{timestamp}.{secrets.token_urlsafe(32)}"
        return value + "." + self._signature(value, session)

    def valid(self, cookie: str, header: str, session: str, *, now: int | None = None) -> bool:
        if (
            not cookie
            or len(cookie) > 256
            or not cookie.isascii()
            or not header.isascii()
            or not hmac.compare_digest(cookie, header)
        ):
            return False
        try:
            stamp, nonce, signature = cookie.split(".")
            age = (int(time.time()) if now is None else now) - int(stamp)
        except ValueError:
            return False
        return (
            0 <= age <= self.ttl
            and len(nonce) == 43
            and hmac.compare_digest(signature, self._signature(stamp + "." + nonce, session))
        )

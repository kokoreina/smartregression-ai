"""Explicit backend settings. Loading settings never connects or reads a .env file."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import parse_qsl, urlsplit

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

from smartregression.adapters.storage.errors import DatabaseConfigurationError

_PREFIX = "SMARTREGRESSION_"
_LOOPBACK = frozenset({"localhost", "127.0.0.1", "::1"})


@dataclass(frozen=True)
class DatabaseSettings:
    # Even the username/host must not be disclosed by settings repr.
    url: URL = field(repr=False)
    connect_timeout_seconds: int = 5
    statement_timeout_ms: int = 10000
    lock_timeout_ms: int = 3000
    allow_loopback_test: bool = False

    def __post_init__(self) -> None:
        url = self.url
        if (
            not isinstance(url, URL)
            or url.drivername != "postgresql+psycopg"
            or not url.host
            or not url.username
            or not url.database
            or any(
                not value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value)
                for value in (url.host, url.username, url.database, url.password or "unused")
            )
            # libpq can interpret dbname containing '=' or a URI as connection
            # options. Only a database name is supported by this boundary.
            or any(c in url.database for c in "=/\\:")
            or any(c.isspace() or c in ",/\\%" for c in url.host)
            or (url.port is not None and not 1 <= url.port <= 65535)
            or type(self.allow_loopback_test) is not bool
        ):
            raise DatabaseConfigurationError()
        if set(url.query) - {"sslmode", "sslrootcert"} or any(
            not isinstance(v, str) or not v.strip() or "\0" in v for v in url.query.values()
        ):
            raise DatabaseConfigurationError()
        sslmode = url.query.get("sslmode", "verify-full")
        if sslmode != "verify-full" and not (
            sslmode == "disable" and self.allow_loopback_test and url.host in _LOOPBACK
        ):
            raise DatabaseConfigurationError()
        if not all(
            type(value) is int and low <= value <= high
            for value, low, high in (
                (self.connect_timeout_seconds, 1, 30),
                (self.statement_timeout_ms, 100, 60000),
                (self.lock_timeout_ms, 1, self.statement_timeout_ms),
            )
        ):
            raise DatabaseConfigurationError()
        object.__setattr__(self, "url", url.update_query_dict({"sslmode": sslmode}))


def load_database_settings(
    environ: Mapping[str, str] | None = None,
    *,
    migration: bool = False,
    allow_loopback_test: bool = False,
) -> DatabaseSettings:
    """Call only for explicit DB work. Runtime never falls back to migration credentials.

    The plaintext loopback exception is a caller option for dedicated tests, not an
    environment toggle that can silently lower production security. Query overrides
    (host, service, options, timeout, etc.) are rejected rather than passed to libpq.
    """
    env = os.environ if environ is None else environ
    key = "MIGRATION_DATABASE_URL" if migration else "DATABASE_URL"
    try:
        raw = env[_PREFIX + key]
        if any(ord(c) < 32 or ord(c) == 127 for c in raw) or urlsplit(raw).fragment:
            raise DatabaseConfigurationError()
        # SQLAlchemy drops blank query values. Preserve their meaning at the raw
        # boundary so an explicit empty TLS setting cannot become an unnoticed default.
        query = parse_qsl(urlsplit(raw).query, keep_blank_values=True, strict_parsing=True)
        if any(not value for _, value in query) or len({k for k, _ in query}) != len(query):
            raise DatabaseConfigurationError()
        return DatabaseSettings(
            url=make_url(raw),
            connect_timeout_seconds=int(env.get(_PREFIX + "DB_CONNECT_TIMEOUT_SECONDS", "5")),
            statement_timeout_ms=int(env.get(_PREFIX + "DB_STATEMENT_TIMEOUT_MS", "10000")),
            lock_timeout_ms=int(env.get(_PREFIX + "DB_LOCK_TIMEOUT_MS", "3000")),
            allow_loopback_test=allow_loopback_test,
        )
    except KeyError, ValueError, TypeError, ArgumentError:
        # URL/parser errors may contain the entire original connection string.
        raise DatabaseConfigurationError() from None

"""Configuration tests do not connect to PostgreSQL."""

import traceback

import pytest

from smartregression.adapters.storage.config import load_database_settings
from smartregression.adapters.storage.errors import DatabaseConfigurationError

PREFIX = "SMARTREGRESSION_"
REMOTE = "postgresql+psycopg://operator:p%40ss%3Aword@db.example.test/analysis"


def test_missing_configuration_is_explicit_and_migration_role_is_separate() -> None:
    with pytest.raises(DatabaseConfigurationError, match="database_configuration_invalid"):
        load_database_settings({})
    env = {PREFIX + "MIGRATION_DATABASE_URL": REMOTE}
    with pytest.raises(DatabaseConfigurationError):
        load_database_settings(env)
    assert load_database_settings(env, migration=True).url.database == "analysis"
    with pytest.raises(DatabaseConfigurationError):
        load_database_settings({PREFIX + "DATABASE_URL": REMOTE}, migration=True)


def test_defaults_and_special_password_never_appear_in_settings_repr() -> None:
    settings = load_database_settings({PREFIX + "DATABASE_URL": REMOTE})
    assert settings.url.password == "p@ss:word"
    assert settings.url.query["sslmode"] == "verify-full"
    assert (settings.connect_timeout_seconds, settings.statement_timeout_ms) == (5, 10000)
    assert settings.lock_timeout_ms == 3000
    for secret in ("operator", "p@ss:word", "p%40ss", "db.example.test", REMOTE):
        assert secret not in repr(settings)


@pytest.mark.parametrize(
    "dsn",
    [
        "sqlite:///local.db",
        "postgresql://user:pass@db.test/db",
        "postgresql+psycopg://user:pass@/db",
        "postgresql+psycopg://db.test/db",
        "postgresql+psycopg://user:pass@db.test/",
        "not-a-url-with-secret",
        "postgresql+psycopg://user:pass@db.test:invalid/db",
        REMOTE + "?sslmode=disable",
        REMOTE + "?sslmode=require",
        REMOTE + "?host=127.0.0.1",
        REMOTE + "?options=-c%20statement_timeout%3D0",
        REMOTE + "?connect_timeout=0",
        REMOTE + "?service=other",
        REMOTE + "?sslmode=verify-full&sslmode=disable",
        REMOTE + "?sslrootcert=",
        REMOTE + "?sslrootcert=system&sslmode=disable",
        "postgresql+psycopg://user:pass@host1,host2/db",
        REMOTE + "#fragment",
        REMOTE.replace("/analysis", "/host%3Devil"),
        REMOTE.replace("/analysis", "/postgresql%3A%2F%2Fevil%2Fdb"),
        REMOTE.replace("operator", "operator%0Ainjected"),
    ],
)
def test_unsafe_or_unsupported_urls_fail_without_echoing_input(dsn: str) -> None:
    with pytest.raises(DatabaseConfigurationError) as caught:
        load_database_settings({PREFIX + "DATABASE_URL": dsn})
    rendered = "".join(traceback.format_exception(caught.value))
    assert dsn not in rendered
    assert str(caught.value) == "database_configuration_invalid"
    assert caught.value.code == "database_configuration_invalid"


def test_loopback_plaintext_is_only_an_explicit_test_exception() -> None:
    for host in ("localhost", "127.0.0.1", "[::1]"):
        env = {PREFIX + "DATABASE_URL": f"postgresql+psycopg://u:p@{host}/db?sslmode=disable"}
        with pytest.raises(DatabaseConfigurationError):
            load_database_settings(env)
        assert (
            load_database_settings(env, allow_loopback_test=True).url.query["sslmode"] == "disable"
        )
    with pytest.raises(DatabaseConfigurationError):
        load_database_settings(
            {PREFIX + "DATABASE_URL": REMOTE + "?sslmode=disable"}, allow_loopback_test=True
        )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("DB_CONNECT_TIMEOUT_SECONDS", "0"),
        ("DB_CONNECT_TIMEOUT_SECONDS", "31"),
        ("DB_CONNECT_TIMEOUT_SECONDS", "1.5"),
        ("DB_CONNECT_TIMEOUT_SECONDS", "true"),
        ("DB_STATEMENT_TIMEOUT_MS", "99"),
        ("DB_STATEMENT_TIMEOUT_MS", "60001"),
        ("DB_LOCK_TIMEOUT_MS", "0"),
        ("DB_LOCK_TIMEOUT_MS", "10001"),
    ],
)
def test_timeouts_are_finite_and_lock_cannot_exceed_statement(name: str, value: str) -> None:
    with pytest.raises(DatabaseConfigurationError):
        load_database_settings({PREFIX + "DATABASE_URL": REMOTE, PREFIX + name: value})


def test_valid_timeout_overrides() -> None:
    settings = load_database_settings(
        {
            PREFIX + "DATABASE_URL": REMOTE,
            PREFIX + "DB_CONNECT_TIMEOUT_SECONDS": "1",
            PREFIX + "DB_STATEMENT_TIMEOUT_MS": "100",
            PREFIX + "DB_LOCK_TIMEOUT_MS": "100",
        }
    )
    assert settings.statement_timeout_ms == settings.lock_timeout_ms == 100


def test_direct_settings_construction_cannot_bypass_security() -> None:
    from sqlalchemy.engine import make_url

    from smartregression.adapters.storage.config import DatabaseSettings

    for kwargs in (
        {"statement_timeout_ms": True},
        {"lock_timeout_ms": 10001},
        {"connect_timeout_seconds": 0},
    ):
        with pytest.raises(DatabaseConfigurationError):
            DatabaseSettings(make_url(REMOTE), **kwargs)

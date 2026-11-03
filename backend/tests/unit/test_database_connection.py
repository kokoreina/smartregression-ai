"""Lifecycle/error tests with a driver double; not real DB acceptance."""

import logging
import subprocess
import sys
import traceback
from contextlib import contextmanager

import pytest
from sqlalchemy.exc import OperationalError

from smartregression.adapters.storage.config import load_database_settings
from smartregression.adapters.storage.connection import database_engine, database_transaction
from smartregression.application.run_store import RunStorageError


class EngineDouble:
    def __init__(self, failure: str | None = None):
        self.events = []
        self.failure = failure

    @contextmanager
    def begin(self):
        self.events.append("begin")
        if self.failure == "connect":
            raise OperationalError("SQL with password", {}, Exception("driver secret"))
        try:
            yield object()
            if self.failure == "commit":
                raise OperationalError("SQL with password", {}, Exception("driver secret"))
        except BaseException:
            self.events.append("rollback")
            raise
        else:
            self.events.append("commit")

    def dispose(self):
        self.events.append("dispose")


def settings():
    return load_database_settings(
        {"SMARTREGRESSION_DATABASE_URL": "postgresql+psycopg://u:secret@db.test/db"}
    )


def test_import_and_engine_creation_do_not_connect(monkeypatch) -> None:
    code = """
import socket
def forbidden(*a, **k): raise AssertionError('network attempted')
socket.socket.connect = forbidden
import psycopg
psycopg.connect = forbidden
from smartregression.adapters.storage.config import load_database_settings
from smartregression.adapters.storage.connection import database_engine
with database_engine(load_database_settings({'SMARTREGRESSION_DATABASE_URL':
    'postgresql+psycopg://u:p@db.test/db'})) as engine:
    assert engine.pool.size() == 2
    assert engine.pool.checkedout() == 0
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=20
    )
    assert result.returncode == 0, result.stderr


def test_real_engine_configuration_is_bounded_without_connecting(monkeypatch) -> None:
    from smartregression.adapters.storage import connection

    captured = {}
    engine = EngineDouble()

    def factory(url, **kwargs):
        captured.update(kwargs)
        return engine

    monkeypatch.setattr(connection, "create_engine", factory)
    with database_engine(settings()) as created:
        assert created is engine
    assert captured["pool_size"] == 2
    assert captured["max_overflow"] == 0
    assert captured["pool_timeout"] == 5
    assert captured["pool_pre_ping"] is True
    assert captured["hide_parameters"] is True
    assert captured["echo"] is False
    assert captured["connect_args"]["connect_timeout"] == 5
    assert captured["connect_args"]["options"] == "-c statement_timeout=10000 -c lock_timeout=3000"
    assert engine.events == ["dispose"]


def test_transaction_commit_and_business_failure_rollback() -> None:
    engine = EngineDouble()
    with database_transaction(engine):
        pass
    assert engine.events == ["begin", "commit"]
    engine.events.clear()
    with pytest.raises(ValueError, match="caller_failure"):
        with database_transaction(engine):
            raise ValueError("caller_failure")
    assert engine.events == ["begin", "rollback"]


@pytest.mark.parametrize("failure", ["connect", "query", "commit"])
def test_database_failures_are_safe_and_not_retried(failure, caplog) -> None:
    engine = EngineDouble(failure)
    with caplog.at_level(logging.DEBUG), pytest.raises(RunStorageError) as caught:
        with database_transaction(engine):
            if failure == "query":
                raise OperationalError(
                    "sensitive SQL", {"password": "secret"}, Exception("driver secret")
                )
    assert engine.events.count("begin") == 1
    assert str(caught.value) == "run_storage_failed"
    rendered = "".join(traceback.format_exception(caught.value)) + caplog.text
    assert "driver secret" not in rendered
    assert "sensitive SQL" not in rendered


def test_engine_disposed_even_when_consumer_fails(monkeypatch) -> None:
    from smartregression.adapters.storage import connection

    engine = EngineDouble()
    monkeypatch.setattr(connection, "create_engine", lambda *a, **k: engine)
    with pytest.raises(ValueError):
        with database_engine(settings()):
            raise ValueError("caller_failure")
    assert engine.events == ["dispose"]


def test_debug_pool_logs_do_not_leak_driver_exceptions(monkeypatch, caplog) -> None:
    import psycopg

    def connect(*args, **kwargs):
        raise psycopg.OperationalError("driver-secret-dsn-with-password")

    monkeypatch.setattr(psycopg, "connect", connect)
    with caplog.at_level(logging.DEBUG, logger="sqlalchemy.pool"), pytest.raises(RunStorageError):
        with database_engine(settings()) as engine, database_transaction(engine):
            pass
    assert "driver-secret-dsn-with-password" not in caplog.text


@pytest.mark.parametrize("logger_name", ["psycopg", "psycopg.transaction", "psycopg.waiting"])
def test_driver_diagnostics_do_not_echo_raw_errors(monkeypatch, caplog, logger_name) -> None:
    import psycopg

    def connect(*args, **kwargs):
        logging.getLogger(logger_name).debug("connection failed: %s", "private-driver-detail")
        raise psycopg.OperationalError("private-driver-detail")

    monkeypatch.setattr(psycopg, "connect", connect)
    with caplog.at_level(logging.DEBUG, logger=logger_name), pytest.raises(RunStorageError):
        with database_engine(settings()) as engine, database_transaction(engine):
            pass
    assert "private-driver-detail" not in caplog.text


def test_driver_logging_policy_is_scoped_to_storage_context(caplog) -> None:
    logger = logging.getLogger("psycopg")
    with caplog.at_level(logging.DEBUG, logger="psycopg"):
        with database_engine(settings()):
            logger.debug("inside-private-detail")
        logger.debug("outside-diagnostic")
    assert "inside-private-detail" not in caplog.text
    assert "outside-diagnostic" in caplog.text


def test_pool_failure_during_dispose_is_sanitized(monkeypatch) -> None:
    from smartregression.adapters.storage import connection

    engine = EngineDouble()

    def dispose():
        raise OperationalError("secret-sql", {}, Exception("secret-driver"))

    engine.dispose = dispose
    monkeypatch.setattr(connection, "create_engine", lambda *a, **k: engine)
    with pytest.raises(RunStorageError) as caught:
        with database_engine(settings()):
            pass
    assert "secret-driver" not in "".join(traceback.format_exception(caught.value))


def test_validated_settings_reach_actual_psycopg_boundary(monkeypatch) -> None:
    import psycopg

    captured = {}

    def connect(*args, **kwargs):
        captured.update(kwargs)
        raise psycopg.OperationalError("synthetic unavailable service")

    monkeypatch.setattr(psycopg, "connect", connect)
    with pytest.raises(RunStorageError):
        with database_engine(settings()) as engine, database_transaction(engine):
            pass
    assert captured["sslmode"] == "verify-full"
    assert captured["connect_timeout"] == 5
    assert captured["options"] == "-c statement_timeout=10000 -c lock_timeout=3000"
    assert captured["dbname"] == "db"
    assert captured["host"] == "db.test"


def test_application_boundary_imports_no_sqlalchemy_or_driver() -> None:
    code = """
import sys
import smartregression.application.run_store
assert 'sqlalchemy' not in sys.modules
assert 'psycopg' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=20
    )
    assert result.returncode == 0, result.stderr


def test_cli_help_and_health_do_not_load_or_require_database_settings() -> None:
    code = """
import os
import sys
from fastapi.testclient import TestClient
from smartregression.api.main import app
from smartregression.cli.main import main
os.environ['SMARTREGRESSION_DATABASE_URL'] = 'invalid-must-not-be-read'
os.environ['SMARTREGRESSION_MIGRATION_DATABASE_URL'] = 'invalid-must-not-be-read'
assert TestClient(app).get('/health').status_code == 200
assert 'sqlalchemy' not in sys.modules
assert 'psycopg' not in sys.modules
sys.argv = ['smartregression', 'analyze', '--help']
main()
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=20
    )
    assert result.returncode == 0, result.stderr

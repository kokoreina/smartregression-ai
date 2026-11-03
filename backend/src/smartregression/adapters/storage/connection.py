"""Synchronous engine/transaction ownership; no schema or startup side effects."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from psycopg import Error as PsycopgError
from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.application.run_store import RunStorageError

_DRIVER_ACTIVE = ContextVar("smartregression_storage_active", default=False)


class _DriverDiagnosticsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _DRIVER_ACTIVE.get()


_DRIVER_FILTER = _DriverDiagnosticsFilter()


@contextmanager
def _driver_diagnostics() -> Iterator[None]:
    # These are the loggers used by the locked synchronous psycopg driver. Filter
    # only this execution context; unrelated threads/driver users retain logging.
    for name in ("psycopg", "psycopg.transaction", "psycopg.waiting"):
        logging.getLogger(name).addFilter(_DRIVER_FILTER)
    token = _DRIVER_ACTIVE.set(True)
    try:
        yield
    finally:
        _DRIVER_ACTIVE.reset(token)


@contextmanager
def database_engine(settings: DatabaseSettings) -> Iterator[Engine]:
    """One explicit owner per command/process; construction is lazy, dispose on exit.

    This is infrastructure for composition/KH setup, not workflow persistence wiring.
    Driver failures are sanitized; SQL values must still be bound parameters.
    """
    # echo=False/hide_parameters do not redact raw driver errors from pool DEBUG
    # logging. Disable only the dedicated infrastructure loggers for these engines;
    # application logs and unrelated SQLAlchemy engines keep their own policy.
    logging.getLogger("sqlalchemy.engine.Engine.smartregression_storage").disabled = True
    logging.getLogger("sqlalchemy.pool.impl.QueuePool.smartregression_storage").disabled = True
    with _driver_diagnostics():
        yield from _engine_context(settings)


def _engine_context(settings: DatabaseSettings) -> Iterator[Engine]:
    try:
        engine = create_engine(
            settings.url,
            logging_name="smartregression_storage",
            pool_logging_name="smartregression_storage",
            poolclass=QueuePool,
            connect_args={
                "connect_timeout": settings.connect_timeout_seconds,
                "options": (
                    f"-c statement_timeout={settings.statement_timeout_ms} "
                    f"-c lock_timeout={settings.lock_timeout_ms}"
                ),
            },
            pool_size=2,
            max_overflow=0,
            pool_timeout=5,
            pool_pre_ping=True,
            hide_parameters=True,
            echo=False,
        )
        try:
            yield engine
        finally:
            engine.dispose()
    except SQLAlchemyError, PsycopgError:
        raise RunStorageError() from None


@contextmanager
def database_transaction(engine: Engine) -> Iterator[Connection]:
    """Commit once on success, rollback on error, and never automatically retry.

    A disconnect during commit is reported as storage failure, including ambiguous
    outcomes. Adapters using this connection must not commit/rollback independently.
    Business exceptions propagate after rollback. Integrity conflicts require domain
    interpretation in the future adapter; raw DB exceptions never leave this boundary.
    """
    with _driver_diagnostics():
        try:
            with engine.begin() as connection:
                yield connection
        except SQLAlchemyError, PsycopgError:
            raise RunStorageError() from None

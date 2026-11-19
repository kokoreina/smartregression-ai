"""Opt-in, isolated native PostgreSQL campaign; never uses the account database.

This supplements, and does not bypass, the existing Docker PostgreSQL 17 harness.
Run with SMARTREGRESSION_NATIVE_PG_BIN pointing to PostgreSQL's bin directory.
"""

import os
import secrets
import socket
import subprocess
from contextlib import ExitStack
from pathlib import Path

import pytest
from backend.tests.integration.storage.conftest import migrated as docker_migrations
from sqlalchemy import text
from sqlalchemy.engine import URL

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="session")
def migrated():
    configured = os.environ.get("SMARTREGRESSION_NATIVE_PG_BIN")
    if not configured:
        pytest.skip("Native campaign is opt-in; set SMARTREGRESSION_NATIVE_PG_BIN")
    binaries = Path(configured).resolve(strict=True)
    suffix = ".exe" if os.name == "nt" else ""
    initdb = binaries / ("initdb" + suffix)
    pgctl = binaries / ("pg_ctl" + suffix)
    assert initdb.is_file() and pgctl.is_file()
    workspace = ROOT / "var" / ("native-reporting-" + secrets.token_hex(8))
    assert workspace.resolve().is_relative_to((ROOT / "var").resolve())
    workspace.mkdir(parents=True)
    password = secrets.token_urlsafe(32)
    pwfile = workspace / "init-password.txt"
    pwfile.write_text(password, encoding="utf-8")

    def run(*args):
        # On Windows the postmaster can inherit PIPE handles from pg_ctl and
        # keep communicate() waiting after pg_ctl exits. Use an owned log file.
        with (workspace / "commands.log").open("ab") as log:
            result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=60)
        # Credentials and raw driver diagnostics must never reach pytest output.
        assert result.returncode == 0, "native_postgres_command_failed"

    try:
        run(
            str(initdb),
            "-D",
            str(workspace / "data"),
            "-U",
            "smartregression_migrator",
            "--pwfile",
            str(pwfile),
            "--auth=scram-sha-256",
            "--encoding=UTF8",
            "--locale=C",
        )
    finally:
        pwfile.unlink(missing_ok=True)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    with (workspace / "data/postgresql.conf").open("a", encoding="utf-8") as stream:
        stream.write(f"\nlisten_addresses='127.0.0.1'\nport={port}\n")
    started = False
    try:
        run(
            str(pgctl),
            "-D",
            str(workspace / "data"),
            "-l",
            str(workspace / "server.log"),
            "-w",
            "-t",
            "30",
            "start",
        )
        started = True
        owner_url = URL.create(
            "postgresql+psycopg",
            username="smartregression_migrator",
            password=password,
            host="127.0.0.1",
            port=port,
            database="postgres",
            query={"sslmode": "disable"},
        )
        runtime_password = secrets.token_urlsafe(32)
        with ExitStack() as stack:
            owner = stack.enter_context(
                database_engine(DatabaseSettings(owner_url, allow_loopback_test=True))
            )
            with owner.begin() as conn:
                assert (
                    Path(conn.scalar(text("SHOW data_directory"))).resolve()
                    == (workspace / "data").resolve()
                )
                # Fresh, campaign-owned cluster; role name is fixed and password is random.
                from psycopg import sql

                raw = conn.connection.driver_connection
                raw.execute(
                    sql.SQL(
                        "CREATE ROLE smartregression_runtime LOGIN PASSWORD {} "
                        "NOSUPERUSER NOCREATEDB NOCREATEROLE"
                    ).format(sql.Literal(runtime_password))
                )
            runtime_url = owner_url.set(
                username="smartregression_runtime", password=runtime_password
            )
            runtime = stack.enter_context(
                database_engine(DatabaseSettings(runtime_url, allow_loopback_test=True))
            )
            # Reuse the exact upgrade/grant logic, not Docker identity/version checks.
            yield docker_migrations.__wrapped__((owner, runtime, owner))
    finally:
        if started:
            run(str(pgctl), "-D", str(workspace / "data"), "-w", "-t", "30", "stop")
        # Keep only this ignored owned cluster for diagnosis; no recursive deletion.

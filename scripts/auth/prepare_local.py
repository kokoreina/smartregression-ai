"""Provision one owned, isolated loopback development DB. Never touch an existing DB.

Keep its labelled container for subsequent local auth testing; no automatic deletion.
The configuration/context files are under ignored var/auth and never printed.
"""

import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy.engine import URL

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine

ROOT = Path(__file__).resolve().parents[2]


def docker(*args, env=None):
    result = subprocess.run(
        ["docker", *args], capture_output=True, timeout=60, env=env, check=False
    )
    if result.returncode:
        raise RuntimeError("local_auth_docker_failed")
    return result.stdout.decode().strip()


def main():
    dest = ROOT / "var/auth"
    dest.mkdir(parents=True, exist_ok=True)
    if any(p.is_symlink() or p.is_junction() for p in (dest, *dest.parents)):
        raise RuntimeError("unsafe_auth_workspace")
    state = dest / "local-context.json"
    config = dest / "web.env"
    if state.exists():
        if not config.exists():
            raise RuntimeError("local_auth_config_incomplete_requires_operator_review")
        previous = json.loads(state.read_text())
        info = json.loads(docker("inspect", previous["container_id"]))[0]
        if info["Config"]["Labels"].get("smartregression.auth-local") != previous["nonce"]:
            raise RuntimeError("local_auth_container_mismatch")
        if not info["State"]["Running"]:
            docker("start", previous["container_id"])
        print("Owned local auth database is running; existing configuration preserved.")
        return 0
    # A pre-existing config must be preserved instead of silently overwritten.
    if config.exists():
        raise RuntimeError("existing_web_config_requires_operator_review")
    nonce = uuid4().hex
    password, runtime_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    image = json.loads((ROOT / "scripts/storage/postgres-image.json").read_text())[
        "linux_amd64_image"
    ]
    container = docker(
        "run",
        "-d",
        "--name",
        "smartregression-auth-local-" + nonce,
        "--label",
        "smartregression.auth-local=" + nonce,
        "--publish",
        "127.0.0.1::5432",
        "--cpus=1",
        "--memory=512m",
        "--pids-limit=128",
        "--env",
        "POSTGRES_PASSWORD",
        "--env",
        "POSTGRES_DB=smartregression_auth_local",
        image,
        env=dict(os.environ, POSTGRES_PASSWORD=password),
    )
    ports = json.loads(docker("inspect", "--format", "{{json .NetworkSettings.Ports}}", container))
    binding = ports["5432/tcp"]
    if len(binding) != 1 or binding[0]["HostIp"] != "127.0.0.1":
        raise RuntimeError("local_auth_binding_mismatch")
    port = int(binding[0]["HostPort"])
    # Record owned container identity before potentially failing readiness/migration.
    state.write_text(json.dumps({"container_id": container, "nonce": nonce}), encoding="utf-8")
    for attempt in range(40):
        try:
            connection = psycopg.connect(
                host="127.0.0.1",
                port=port,
                user="postgres",
                password=password,
                dbname="smartregression_auth_local",
                connect_timeout=2,
                autocommit=True,
            )
            break
        except psycopg.Error:
            if attempt == 39:
                raise RuntimeError("local_auth_postgresql_not_ready") from None
            time.sleep(0.5)
    with connection:
        connection.execute(
            sql.SQL("CREATE ROLE smartregression_web_runtime LOGIN PASSWORD {}").format(
                sql.Literal(runtime_password)
            )
        )
    migration_url = URL.create(
        "postgresql+psycopg",
        username="postgres",
        password=password,
        host="127.0.0.1",
        port=port,
        database="smartregression_auth_local",
        query={"sslmode": "disable"},
    )
    settings = DatabaseSettings(migration_url, allow_loopback_test=True)
    with database_engine(settings) as engine, engine.connect() as conn:
        cfg = Config(str(ROOT / "alembic.ini"))
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
    with psycopg.connect(
        host="127.0.0.1",
        port=port,
        user="postgres",
        password=password,
        dbname="smartregression_auth_local",
        autocommit=True,
    ) as conn:
        conn.execute("GRANT USAGE ON SCHEMA smartregression TO smartregression_web_runtime")
        conn.execute(
            "GRANT SELECT,INSERT,UPDATE ON smartregression.web_users, "
            "smartregression.web_sessions, smartregression.web_account_tokens, "
            "smartregression.web_rate_limits TO smartregression_web_runtime"
        )
    runtime_url = migration_url.set(
        username="smartregression_web_runtime", password=runtime_password
    )
    config.write_text(
        "SMARTREGRESSION_AUTH_LOCAL_HTTP=1\nSMARTREGRESSION_FRONTEND_ORIGIN=http://127.0.0.1:5173\n"
        + "SMARTREGRESSION_CSRF_SECRET="
        + secrets.token_urlsafe(48)
        + "\n"
        + "SMARTREGRESSION_DATABASE_URL="
        + runtime_url.render_as_string(hide_password=False)
        + "\n"
        + "SMARTREGRESSION_MIGRATION_DATABASE_URL="
        + migration_url.render_as_string(hide_password=False)
        + "\n"
        + "SMARTREGRESSION_SMTP_USERNAME=\nSMARTREGRESSION_SMTP_PASSWORD=\n",
        encoding="utf-8",
    )
    print("Created isolated local auth DB and var/auth/web.env. Fill Gmail fields privately.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(
            "Local auth preparation failed; inspect owned container/config privately.",
            file=sys.stderr,
        )
        sys.exit(1)

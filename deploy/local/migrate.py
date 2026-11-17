"""Explicit operator composition: migration role and least-privilege runtime role.

This command belongs to an isolated setup job, never backend startup. Arguments and
logs do not carry credentials. It only acts on the dedicated Compose database.
"""

import json
import os
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql

from smartregression.adapters.storage.config import load_database_settings
from smartregression.adapters.storage.connection import database_engine


def main():
    settings = load_database_settings(migration=True)
    if settings.url.host != "db" or settings.url.database != "smartregression_product":
        raise ValueError("compose_database_required")
    with database_engine(settings) as engine:
        with engine.connect() as connection:
            config = Config("/app/alembic.ini")
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
    options = settings.url
    with psycopg.connect(
        host=options.host,
        dbname=options.database,
        user=options.username,
        password=options.password,
        sslmode="verify-full",
        sslrootcert=options.query["sslrootcert"],
    ) as connection:
        role = "smartregression_product_runtime"
        exists = connection.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone()
        if not exists:
            connection.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE"
                ).format(
                    sql.Identifier(role),
                    sql.Literal(os.environ["SMARTREGRESSION_RUNTIME_DB_PASSWORD"]),
                )
            )
        connection.execute(
            sql.SQL("GRANT USAGE ON SCHEMA smartregression TO {}").format(sql.Identifier(role))
        )
        mutable = [
            "web_users",
            "web_sessions",
            "web_account_tokens",
            "web_rate_limits",
            "web_projects",
            "web_runs",
            "web_ai_requests",
            "web_notes",
            "web_view_states",
        ]
        immutable = [
            "repositories",
            "snapshots",
            "analysis_runs",
            "artifacts",
            "run_reports",
            "evidence_bundles",
            "run_stage_payloads",
            "web_activity",
            "web_explorer_snapshots",
            "web_scenarios",
        ]
        for table in mutable:
            connection.execute(
                sql.SQL("GRANT SELECT,INSERT,UPDATE ON smartregression.{} TO {}").format(
                    sql.Identifier(table), sql.Identifier(role)
                )
            )
        for table in immutable:
            connection.execute(
                sql.SQL("GRANT SELECT,INSERT ON smartregression.{} TO {}").format(
                    sql.Identifier(table), sql.Identifier(role)
                )
            )
        for table in ["web_ai_campaigns", "web_ai_grants"]:
            connection.execute(
                sql.SQL("GRANT SELECT ON smartregression.{} TO {}").format(
                    sql.Identifier(table), sql.Identifier(role)
                )
            )
        connection.execute(
            sql.SQL(
                "GRANT SELECT,INSERT,DELETE ON smartregression.web_reporting_views TO {}"
            ).format(sql.Identifier(role))
        )
    root = Path("/app/var")
    for directory in [root, root / "web-reports", root / "web-ai", root / "web-repositories"]:
        directory.mkdir(exist_ok=True)
        os.chown(directory, 10001, 10001)
    print(json.dumps({"migrated": True, "runtime_ddl": False, "scope": "owned compose database"}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Compose migration failed; private details withheld.") from None

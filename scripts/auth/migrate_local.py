"""Back up and upgrade only the labelled development database created by prepare_local.

No external DSN or database name is accepted. Private env/context values never print.
"""

import json
import subprocess
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine
from smartregression.auth_config import web_environment

ROOT = Path(__file__).resolve().parents[2]


def main():
    directory = ROOT / "var/auth"
    if any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)):
        raise ValueError("unsafe_workspace")
    context = json.loads((directory / "local-context.json").read_text())
    inspected = subprocess.run(
        ["docker", "inspect", context["container_id"]],
        capture_output=True,
        check=True,
        timeout=15,
    )
    info = json.loads(inspected.stdout)[0]
    if info["Config"]["Labels"].get("smartregression.auth-local") != context["nonce"]:
        raise ValueError("container_ownership_mismatch")
    bindings = info["NetworkSettings"]["Ports"]["5432/tcp"]
    env = web_environment()
    url = make_url(env["SMARTREGRESSION_MIGRATION_DATABASE_URL"])
    if (
        len(bindings) != 1
        or bindings[0]["HostIp"] != "127.0.0.1"
        or str(url.port) != bindings[0]["HostPort"]
        or url.host != "127.0.0.1"
        or url.database != "smartregression_auth_local"
        or url.username != "postgres"
    ):
        raise ValueError("development_database_mismatch")
    backup = subprocess.run(
        [
            "docker",
            "exec",
            context["container_id"],
            "pg_dump",
            "-U",
            "postgres",
            "-d",
            "smartregression_auth_local",
            "--format=custom",
            "--no-owner",
            "--no-acl",
        ],
        capture_output=True,
        check=True,
        timeout=60,
    )
    (directory / ("before-upgrade-" + uuid4().hex + ".dump")).write_bytes(backup.stdout)
    with database_engine(DatabaseSettings(url, allow_loopback_test=True)) as engine:
        with engine.connect() as connection:
            cfg = Config(str(ROOT / "alembic.ini"))
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "GRANT SELECT,INSERT,UPDATE ON smartregression.web_projects, "
                    "smartregression.web_runs,smartregression.web_notes, "
                    "smartregression.web_view_states TO smartregression_web_runtime"
                )
            )
            connection.execute(
                text(
                    "GRANT SELECT,INSERT ON smartregression.web_activity, "
                    "smartregression.repositories, smartregression.snapshots, "
                    "smartregression.analysis_runs, smartregression.artifacts, "
                    "smartregression.run_reports, smartregression.evidence_bundles, "
                    "smartregression.run_stage_payloads, smartregression.web_explorer_snapshots, "
                    "smartregression.web_scenarios "
                    "TO smartregression_web_runtime"
                )
            )
            connection.execute(
                text(
                    "GRANT SELECT ON smartregression.web_ai_campaigns, "
                    "smartregression.web_ai_grants "
                    "TO smartregression_web_runtime"
                )
            )
            connection.execute(
                text(
                    "GRANT SELECT,INSERT,UPDATE ON smartregression.web_ai_requests "
                    "TO smartregression_web_runtime"
                )
            )
            connection.execute(
                text(
                    "GRANT SELECT,INSERT,DELETE ON smartregression.web_reporting_views "
                    "TO smartregression_web_runtime"
                )
            )
    print("Owned development database backed up, migrated and runtime grants verified.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Development upgrade failed; private details withheld.") from None

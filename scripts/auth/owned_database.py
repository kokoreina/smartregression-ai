"""Private operator boundary for the exact labelled local development database."""

import json
import subprocess
from pathlib import Path

from sqlalchemy.engine import make_url

from smartregression.auth_config import web_environment

ROOT = Path(__file__).resolve().parents[2]


def owned_database():
    directory = ROOT / "var/auth"
    if any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)):
        raise ValueError("unsafe_workspace")
    context = json.loads((directory / "local-context.json").read_text())
    url = make_url(web_environment()["SMARTREGRESSION_MIGRATION_DATABASE_URL"])
    info = json.loads(
        subprocess.check_output(["docker", "inspect", context["container_id"]], timeout=15)
    )[0]
    if (
        info["Config"]["Labels"].get("smartregression.auth-local") != context["nonce"]
        or info["NetworkSettings"]["Ports"]["5432/tcp"]
        != [{"HostIp": "127.0.0.1", "HostPort": str(url.port)}]
        or url.host != "127.0.0.1"
        or url.database != "smartregression_auth_local"
        or url.username != "postgres"
    ):
        raise ValueError("owned_database_required")
    return url, context

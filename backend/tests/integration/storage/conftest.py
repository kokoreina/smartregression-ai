"""Only the opt-in harness-created PostgreSQL container may supply DB fixtures."""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import URL

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="session")
def storage_context():
    raw = os.environ.get("SMARTREGRESSION_KH_TEST_CONTEXT")
    if raw is None:
        pytest.skip("Run scripts/storage/verify.ps1 for a dedicated real PostgreSQL test container")
    context = json.loads(raw)
    assert re.fullmatch(r"[a-f0-9]{64}", context["container_id"])
    assert re.fullmatch(r"[a-f0-9]{32}", context["nonce"])
    labels = json.loads(
        subprocess.check_output(
            ["docker", "inspect", "--format", "{{json .Config.Labels}}", context["container_id"]],
            timeout=15,
        )
    )
    assert labels.get("smartregression.kh-storage-test") == context["nonce"]
    ports = json.loads(
        subprocess.check_output(
            [
                "docker",
                "inspect",
                "--format",
                "{{json .NetworkSettings.Ports}}",
                context["container_id"],
            ],
            timeout=15,
        )
    )
    assert ports["5432/tcp"] == [{"HostIp": "127.0.0.1", "HostPort": str(context["port"])}]
    return context


@pytest.fixture(scope="session")
def engines(storage_context):
    def settings(user, password_key, database="smartregression_kh_test"):
        return DatabaseSettings(
            URL.create(
                "postgresql+psycopg",
                username=user,
                password=storage_context[password_key],
                host="127.0.0.1",
                port=storage_context["port"],
                database=database,
                query={"sslmode": "disable"},
            ),
            allow_loopback_test=True,
        )

    with (
        database_engine(settings("smartregression_migrator", "migration_password")) as owner,
        database_engine(settings("smartregression_runtime", "runtime_password")) as runtime,
        database_engine(
            settings("smartregression_migrator", "migration_password", "smartregression_kh_failure")
        ) as failure,
    ):
        with owner.connect() as connection:
            assert (
                connection.scalar(sa.text("SELECT current_database()")) == "smartregression_kh_test"
            )
            assert int(connection.scalar(sa.text("SHOW server_version_num"))) // 10000 == 17
        yield owner, runtime, failure


def alembic_config(connection):
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["connection"] = connection
    return config


@pytest.fixture(scope="session")
def migrated(engines):
    owner, runtime, failure = engines
    with owner.connect() as connection:
        command.upgrade(alembic_config(connection), "20261103_01")
    with owner.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO smartregression.repositories "
                "(repository_id,source_kind) VALUES ('upgrade-sentinel','local')"
            )
        )
    with owner.connect() as connection:
        command.upgrade(alembic_config(connection), "head")
        command.upgrade(alembic_config(connection), "head")
    with owner.begin() as connection:
        assert (
            connection.scalar(
                sa.text(
                    "SELECT count(*) FROM smartregression.repositories "
                    "WHERE repository_id='upgrade-sentinel'"
                )
            )
            == 1
        )
        connection.execute(
            sa.text("GRANT USAGE ON SCHEMA smartregression TO smartregression_runtime")
        )
        connection.execute(
            sa.text(
                "GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA smartregression "
                "TO smartregression_runtime"
            )
        )
        connection.execute(
            sa.text("REVOKE ALL ON smartregression.alembic_version FROM smartregression_runtime")
        )
    return owner, runtime, failure

"""Create one labelled disposable PostgreSQL container; never accept an external DSN.

Credentials are random, memory-only and never recorded in artifacts or command argv.
Only the exact container created and verified by this invocation may be removed.
"""

import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from recovery_fixture import seed_recovery_fixture

from smartregression.adapters.bounded_process import bounded_command

PROJECT = Path(__file__).resolve().parents[2]


def docker(*args: str, timeout: int = 30, env=None) -> bytes:
    return bounded_command(["docker", *args], timeout, 8 * 1024 * 1024, env=env, merge_stderr=False)


def connect(context, *, database="smartregression_kh_test"):
    return psycopg.connect(
        host="127.0.0.1",
        port=context["port"],
        user="postgres",
        password=context["admin_password"],
        dbname=database,
        connect_timeout=3,
        sslmode="disable",
        autocommit=True,
    )


def snapshot_rows(connection):
    result = {}
    for name in (
        "repositories",
        "snapshots",
        "analysis_runs",
        "artifacts",
        "run_reports",
        "evidence_bundles",
        "test_inventories",
        "test_cases",
        "knowledge_indexes",
        "index_chunks",
        "alembic_version",
    ):
        rows = connection.execute(
            sql.SQL("SELECT row_to_json(t)::text FROM smartregression.{} t").format(
                sql.Identifier(name)
            )
        ).fetchall()
        result[name] = sorted(row[0] for row in rows)
    return result


def execute():
    nonce = uuid4().hex
    output = PROJECT / "var" / ("storage-verification-" + nonce)
    if any(path.is_symlink() or path.is_junction() for path in (output, *output.parents)):
        raise ValueError("unsafe_storage_test_output")
    output.mkdir(parents=True, exist_ok=False)
    image = json.loads((PROJECT / "scripts/storage/postgres-image.json").read_text())[
        "linux_amd64_image"
    ]
    evidence = {
        "scope": "dedicated_owned_postgresql_fixture",
        "image": image,
        "started_at": datetime.now(UTC).isoformat(),
        "checks": {},
        "passed": False,
    }
    context = {
        "nonce": nonce,
        "admin_password": secrets.token_urlsafe(32),
        "migration_password": secrets.token_urlsafe(32),
        "runtime_password": secrets.token_urlsafe(32),
    }
    container = None
    try:
        docker("pull", image, timeout=300)
        env = dict(os.environ, POSTGRES_PASSWORD=context["admin_password"])
        container = (
            docker(
                "run",
                "-d",
                "--name",
                "smartregression-kh-storage-" + nonce,
                "--label",
                "smartregression.kh-storage-test=" + nonce,
                "--publish",
                "127.0.0.1::5432",
                "--cpus=1",
                "--memory=512m",
                "--pids-limit=128",
                "--env",
                "POSTGRES_PASSWORD",
                "--env",
                "POSTGRES_DB=smartregression_kh_test",
                image,
                env=env,
            )
            .decode()
            .strip()
        )
        context["container_id"] = container
        ports = json.loads(
            docker("inspect", "--format", "{{json .NetworkSettings.Ports}}", container)
        )
        assert ports["5432/tcp"][0]["HostIp"] == "127.0.0.1"
        context["port"] = int(ports["5432/tcp"][0]["HostPort"])
        evidence["container_id"] = container
        evidence["image_id"] = (
            docker("inspect", "--format", "{{.Image}}", container).decode().strip()
        )
        ready = False
        for _ in range(40):
            try:
                with connect(context) as connection:
                    evidence["postgresql_version"] = connection.execute(
                        "SELECT version()"
                    ).fetchone()[0]
                    assert (
                        int(connection.execute("SHOW server_version_num").fetchone()[0]) // 10000
                        == 17
                    )
                    ready = True
                    break
            except psycopg.OperationalError:
                time.sleep(0.5)
        if not ready:
            raise RuntimeError("postgresql_fixture_not_ready")
        with connect(context) as connection:
            for role, password in (
                ("smartregression_migrator", context["migration_password"]),
                ("smartregression_runtime", context["runtime_password"]),
            ):
                connection.execute(
                    sql.SQL(
                        "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE"
                    ).format(sql.Identifier(role), sql.Literal(password))
                )
            connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
            connection.execute(
                "GRANT CREATE ON DATABASE smartregression_kh_test TO smartregression_migrator"
            )
            for name in (
                "smartregression_kh_failure",
                "smartregression_kh_restore",
                "smartregression_kh_fresh",
            ):
                connection.execute(
                    sql.SQL("CREATE DATABASE {} OWNER smartregression_migrator").format(
                        sql.Identifier(name)
                    )
                )
        with connect(context, database="smartregression_kh_fresh") as connection:
            connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        test_env = dict(
            os.environ,
            SMARTREGRESSION_KH_TEST_CONTEXT=json.dumps(context),
            PYTHONPATH=str(PROJECT / "backend/src"),
        )
        # Keep Git templates below MAX_PATH; use an invocation-owned short workspace.
        index_root = PROJECT / "var" / ("x-" + nonce)
        index_root.mkdir()
        test_env["SMARTREGRESSION_INDEX_TEST_ROOT"] = str(index_root)
        evidence["index_test_workspace"] = str(index_root)
        test = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "backend/tests/integration/storage",
                "-q",
                "--tb=line",
                "-p",
                "no:cacheprovider",
                "--junitxml",
                str(output / "postgresql-tests.xml"),
                "--basetemp",
                str(index_root / "t"),
            ],
            cwd=PROJECT,
            env=test_env,
            timeout=180,
            check=False,
        )
        evidence["checks"]["postgresql_pytest_exit"] = test.returncode
        if test.returncode:
            raise RuntimeError("postgresql_integration_failed")
        # Fresh-at-head is separate from the populated M001 -> M002 upgrade exercised by pytest.
        from alembic import command
        from alembic.config import Config
        from sqlalchemy.engine import URL

        from smartregression.adapters.storage.config import DatabaseSettings
        from smartregression.adapters.storage.connection import database_engine

        settings = DatabaseSettings(
            URL.create(
                "postgresql+psycopg",
                username="smartregression_migrator",
                password=context["migration_password"],
                host="127.0.0.1",
                port=context["port"],
                database="smartregression_kh_fresh",
                query={"sslmode": "disable"},
            ),
            allow_loopback_test=True,
        )
        config = Config(str(PROJECT / "alembic.ini"))
        config.attributes["migration_settings"] = settings
        command.upgrade(config, "head")
        evidence["checks"]["fresh_head"] = True
        artifact_root = output / "artifacts"
        with database_engine(settings) as engine, engine.begin() as connection:
            descriptor = seed_recovery_fixture(connection, artifact_root)
        # No writers are active now. Back up this complete metadata+artifact fixture,
        # not the intentionally incomplete negative constraint-test rows.
        dump = docker(
            "exec",
            container,
            "pg_dump",
            "-U",
            "postgres",
            "-d",
            "smartregression_kh_fresh",
            "--schema=smartregression",
            "--format=custom",
            "--no-owner",
            "--no-acl",
        )
        (output / "foundation.dump").write_bytes(dump)
        restore = subprocess.run(
            [
                "docker",
                "exec",
                "-i",
                container,
                "pg_restore",
                "-U",
                "postgres",
                "-d",
                "smartregression_kh_restore",
                "--exit-on-error",
                "--no-owner",
                "--no-acl",
            ],
            input=dump,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if restore.returncode:
            raise RuntimeError("restore_failed")
        with (
            connect(context, database="smartregression_kh_fresh") as original,
            connect(context, database="smartregression_kh_restore") as restored,
        ):
            assert snapshot_rows(original) == snapshot_rows(restored)
        evidence["checks"]["backup_restore_exact_rows"] = True
        restored_root = output / "restored-artifacts"
        shutil.copytree(artifact_root, restored_root)
        restored_bytes = (restored_root / descriptor["storage_key"]).read_bytes()
        assert len(restored_bytes) == descriptor["size_bytes"]
        assert hashlib.sha256(restored_bytes).hexdigest() == descriptor["sha256"]
        with connect(context, database="smartregression_kh_restore") as restored:
            row = restored.execute(
                "SELECT storage_key,sha256,size_bytes FROM smartregression.artifacts"
            ).fetchone()
            assert row == (
                descriptor["storage_key"],
                descriptor["sha256"],
                descriptor["size_bytes"],
            )
            from smartregression.application.evidence_store import decode_evidence
            from smartregression.contracts.stages import RunIdentity

            bundle_row = restored.execute(
                "SELECT payload,bundle_format,payload_sha256 FROM smartregression.evidence_bundles"
            ).fetchone()
            restored_bundle = decode_evidence(
                *bundle_row, RunIdentity.model_validate(descriptor["evidence_identity"])
            )
            assert restored_bundle.identity.run_id == "recovery-run"
        evidence["checks"]["evidence_restore_decode_and_identity"] = True
        from smartregression.adapters.storage.index_artifacts import IndexArtifactFiles
        from smartregression.adapters.storage.index_store import BoundIndexStore
        from smartregression.application.index_store import decode_index_record

        restored_settings = DatabaseSettings(
            URL.create(
                "postgresql+psycopg",
                username="postgres",
                password=context["admin_password"],
                host="127.0.0.1",
                port=context["port"],
                database="smartregression_kh_restore",
                query={"sslmode": "disable"},
            ),
            allow_loopback_test=True,
        )
        original_record = decode_index_record(descriptor["index_record"])
        with database_engine(restored_settings) as engine, engine.begin() as connection:
            restored_index = BoundIndexStore(connection).load(original_record.key)
            assert restored_index.state == "ready" and restored_index.record == original_record
        restored_index_files = IndexArtifactFiles(
            restored_root,
            source_repository=output / "recovery-index-source",
        )
        assert hashlib.sha256(restored_index_files.read(original_record)).hexdigest() == (
            original_record.artifact_sha256
        )
        evidence["checks"]["index_metadata_chunks_artifact_restore"] = True
        evidence["checks"]["artifact_restore_digest_and_catalog"] = True
        evidence["backup_sha256"] = hashlib.sha256(dump).hexdigest()
        evidence["checks"]["revision_head"] = "20261105_05"
        evidence["passed"] = True
    except Exception as exc:
        # Do not echo SQL, credentials or exception chains at this operator boundary.
        safe = {"postgresql_fixture_not_ready", "postgresql_integration_failed", "restore_failed"}
        evidence["error_code"] = str(exc) if str(exc) in safe else "storage_verification_failed"
    finally:
        if container is not None:
            try:
                labels = json.loads(
                    docker("inspect", "--format", "{{json .Config.Labels}}", container)
                )
                if labels.get("smartregression.kh-storage-test") != nonce:
                    raise RuntimeError("container_ownership_mismatch")
                docker("rm", "-f", "-v", container)
                evidence["checks"]["owned_container_removed"] = True
            except Exception:
                evidence["passed"] = False
                evidence["error_code"] = "storage_test_cleanup_failed"
        evidence["finished_at"] = datetime.now(UTC).isoformat()
        (output / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps({"passed": evidence["passed"], "evidence": str(output / "evidence.json")}))
    return 0 if evidence["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(execute())

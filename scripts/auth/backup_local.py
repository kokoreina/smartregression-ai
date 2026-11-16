"""Consistent owned-DB backup, seven local copies, isolated restore and API readback.

No runtime account receives DDL. No off-host backup claim; no original DB restore.
All deletion is confined to recognized artifacts in this exact backup directory.
"""

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from uuid import uuid4

import psycopg
from owned_database import ROOT, owned_database
from psycopg import sql


def checksums(connection):
    tables = connection.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='smartregression' "
        "AND table_type='BASE TABLE' ORDER BY table_name"
    ).fetchall()
    output = {}
    for (table,) in tables:
        rows = connection.execute(
            sql.SQL(
                "SELECT row_to_json(t)::text FROM smartregression.{} t "
                "ORDER BY row_to_json(t)::text"
            ).format(sql.Identifier(table))
        ).fetchall()
        output[table] = {
            "count": len(rows),
            "sha256": hashlib.sha256("\n".join(row[0] for row in rows).encode()).hexdigest(),
        }
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore-check", action="store_true")
    args = parser.parse_args()
    url, context = owned_database()
    directory = ROOT / "var/backups"
    if any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)):
        raise ValueError("unsafe_workspace")
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex
    base = directory / ("backup-" + stamp)

    def connect(database):
        return psycopg.connect(
            host=url.host,
            port=url.port,
            user=url.username,
            password=url.password,
            dbname=database,
            autocommit=True,
        )

    with connect(url.database) as connection:
        with connection.transaction():
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            snapshot = connection.execute("SELECT pg_export_snapshot()").fetchone()[0]
            expected = checksums(connection)
            dump = subprocess.run(
                [
                    "docker",
                    "exec",
                    context["container_id"],
                    "pg_dump",
                    "-U",
                    "postgres",
                    "-d",
                    url.database,
                    "--format=custom",
                    "--no-owner",
                    "--no-acl",
                    "--snapshot",
                    snapshot,
                ],
                capture_output=True,
                timeout=120,
                check=True,
            ).stdout
    dump_path = base.with_suffix(".dump")
    dump_path.write_bytes(dump)
    report_root = ROOT / "var/web-reports"
    manifest = {}
    archive_path = base.with_suffix(".zip")
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        if report_root.exists():
            if any(p.is_symlink() or p.is_junction() for p in (report_root, *report_root.parents)):
                raise ValueError("unsafe_artifact_root")
            for file in report_root.rglob("*"):
                if file.is_symlink() or file.is_junction():
                    raise ValueError("unsafe_artifact")
                if file.is_file():
                    if not file.resolve().is_relative_to(report_root.resolve()):
                        raise ValueError("unsafe_artifact")
                    raw = file.read_bytes()
                    name = file.relative_to(report_root).as_posix()
                    manifest[name] = hashlib.sha256(raw).hexdigest()
                    archive.writestr(name, raw)
    result = {
        "scope": "owned local database and immutable report artifacts; not off-host",
        "created_at": datetime.now(UTC).isoformat(),
        "dump_sha256": hashlib.sha256(dump).hexdigest(),
        "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "tables": expected,
        "artifacts": manifest,
        "restore_verified": False,
    }
    if args.restore_check:
        name = "sr_restore_" + uuid4().hex
        with connect(url.database) as admin:
            admin.execute(sql.SQL("CREATE DATABASE {} OWNER postgres").format(sql.Identifier(name)))
            try:
                subprocess.run(
                    [
                        "docker",
                        "exec",
                        "-i",
                        context["container_id"],
                        "pg_restore",
                        "-U",
                        "postgres",
                        "-d",
                        name,
                        "--no-owner",
                        "--no-acl",
                        "--exit-on-error",
                    ],
                    input=dump,
                    capture_output=True,
                    timeout=120,
                    check=True,
                )
                with connect(name) as restored:
                    if checksums(restored) != expected:
                        raise ValueError("restore_counts_or_hash_mismatch")
                    projects = restored.execute(
                        "SELECT owner_id,id FROM smartregression.web_projects ORDER BY id LIMIT 1"
                    ).fetchone()
                with zipfile.ZipFile(archive_path) as archive:
                    for path, digest in manifest.items():
                        if hashlib.sha256(archive.read(path)).hexdigest() != digest:
                            raise ValueError("artifact_hash_mismatch")
                if projects:
                    from smartregression.adapters.storage.config import DatabaseSettings
                    from smartregression.adapters.storage.connection import database_engine
                    from smartregression.adapters.storage.project_store import PostgresProjectStore
                    from smartregression.application.projects import ProjectService

                    with database_engine(
                        DatabaseSettings(url.set(database=name), allow_loopback_test=True)
                    ) as engine:
                        service = ProjectService(PostgresProjectStore(engine), None, None)
                        if str(service.get(str(projects[0]), str(projects[1])).id) != str(
                            projects[1]
                        ):
                            raise ValueError("application_readback_failed")
                result["restore_verified"] = True
                result["application_project_readback"] = bool(projects)
            finally:
                if not re.fullmatch("sr_restore_[0-9a-f]{32}", name):
                    raise ValueError("unsafe_restore_database")
                admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
    base.with_suffix(".json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    # Only recognized complete backups created by this tool, no recursive deletion.
    bundles = sorted(directory.glob("backup-*.json"), key=lambda p: p.name, reverse=True)
    for old in bundles[7:]:
        if not re.fullmatch("backup-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{32}", old.stem):
            continue
        for suffix in [".json", ".dump", ".zip"]:
            file = old.with_suffix(suffix)
            if (
                file.exists()
                and not file.is_symlink()
                and file.resolve().parent == directory.resolve()
            ):
                file.unlink()
    print(
        json.dumps(
            {
                "backed_up": True,
                "restore_verified": result["restore_verified"],
                "artifact": str(base.with_suffix(".json")),
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Owned local backup failed; private details withheld.") from None

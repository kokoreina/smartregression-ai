"""Disposable local browser fixture: real PostgreSQL + SMTP, synthetic GitHub input.

Uses only the previously labelled development container. Creates its own random DB
and runtime role, never migrates the user's database. Inbox endpoint exists only
in this test entrypoint, bound to loopback. Never expose this fixture publicly.
"""

import json
import mimetypes
import os
import re
import smtplib
import subprocess
from contextlib import ExitStack, contextmanager
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
from uuid import uuid4

import psycopg
import uvicorn
from aiosmtpd.controller import Controller
from alembic import command
from alembic.config import Config
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.engine import make_url

from smartregression.adapters.auth_security import PasswordHasher, token_hash
from smartregression.adapters.storage.analysis_store import PostgresAnalysisStore
from smartregression.adapters.storage.auth_store import PostgresAuthStore
from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine
from smartregression.adapters.storage.project_store import PostgresProjectStore
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.adapters.storage.web_run_store import PostgresWebRunStore
from smartregression.api.main import create_app
from smartregression.application.auth import AuthService
from smartregression.application.persistence import bundle_from_report, persist_report
from smartregression.application.projects import ProjectService
from smartregression.application.repository_analysis import RepositoryService
from smartregression.application.web_runs import WebRunService
from smartregression.auth_config import AuthSettings, web_environment

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = os.environ.get("SMARTREGRESSION_E2E_ORIGIN", "http://127.0.0.1:8150")
if ORIGIN not in {"http://127.0.0.1:8150", "https://localhost:8444"}:
    raise ValueError("test_origin_not_allowed")


class Inbox:
    def __init__(self):
        self.messages = []

    async def handle_DATA(self, server, session, envelope):
        message = BytesParser(policy=policy.default).parsebytes(envelope.content)
        self.messages.append({"to": str(message["To"]), "body": message.get_content()})
        return "250 accepted"


class TestSmtp:
    def send(self, email, purpose, token):
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = "test@example.com", email, purpose
        path = "verify-email" if purpose == "verify" else "reset-password"
        message.set_content(ORIGIN + "/" + path + "#token=" + token)
        with smtplib.SMTP("127.0.0.1", 8151, timeout=5) as smtp:
            smtp.send_message(message)


def main():
    from backend.tests.unit.test_repository_web import FILES, remote

    from smartregression.adapters.parsers.javascript import parse_javascript
    from smartregression.adapters.storage.explorer_store import PostgresExplorerStore
    from smartregression.adapters.storage.note_store import PostgresNoteStore
    from smartregression.adapters.storage.scenario_store import PostgresScenarioStore
    from smartregression.adapters.storage.web_ai_store import PostgresAiStore
    from smartregression.application.explorer import ExplorerService
    from smartregression.application.notes import NoteService
    from smartregression.application.scenarios import ScenarioService
    from smartregression.application.web_ai import WebAiService
    from smartregression.contracts.repository import NarrativeResult

    FILES.update(
        {
            "payment.js": b"export function pay(){ return 1; }\n",
            "checkout.js": (
                b'import {pay} from "./payment.js";\nexport function checkout(){ return pay(); }\n'
            ),
        }
    )
    if os.environ.get("SMARTREGRESSION_E2E_LARGE_GRAPH") == "1":
        for index in range(80):
            prefix = f'import {{run as previous}} from "./module{index - 1}.js";\n' if index else ""
            FILES[f"module{index}.js"] = (
                prefix
                + "export function run(){ return "
                + ("previous()" if index else "1")
                + "; }\n"
            ).encode()

    # Windows registry mappings can incorrectly label .js as text/plain.
    mimetypes.add_type("application/javascript", ".js")

    context = json.loads((ROOT / "var/auth/local-context.json").read_text())
    env = web_environment()
    admin_url = make_url(env["SMARTREGRESSION_MIGRATION_DATABASE_URL"])
    info = json.loads(
        subprocess.check_output(["docker", "inspect", context["container_id"]], timeout=15)
    )[0]
    binding = info["NetworkSettings"]["Ports"]["5432/tcp"]
    if (
        info["Config"]["Labels"].get("smartregression.auth-local") != context["nonce"]
        or binding != [{"HostIp": "127.0.0.1", "HostPort": str(admin_url.port)}]
        or admin_url.database != "smartregression_auth_local"
        or admin_url.host != "127.0.0.1"
    ):
        raise RuntimeError("owned_fixture_database_required")
    nonce = uuid4().hex
    name, password = "sr_e2e_" + nonce, uuid4().hex + uuid4().hex
    root = ROOT / "var/phase3-8" / name
    root.mkdir(parents=True)
    source, artifacts = root / "source", root / "reports"
    source.mkdir()
    artifacts.mkdir()
    if any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)):
        raise RuntimeError("unsafe_test_workspace")
    admin = psycopg.connect(
        host=admin_url.host,
        port=admin_url.port,
        user=admin_url.username,
        password=admin_url.password,
        dbname=admin_url.database,
        autocommit=True,
    )
    created = False
    smtp = None
    try:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE").format(
                sql.Identifier(name), sql.Literal(password)
            )
        )
        admin.execute(sql.SQL("CREATE DATABASE {} OWNER postgres").format(sql.Identifier(name)))
        created = True
        migration = admin_url.set(database=name)
        runtime = migration.set(username=name, password=password)
        with ExitStack() as stack:
            migrator = stack.enter_context(
                database_engine(DatabaseSettings(migration, allow_loopback_test=True))
            )
            with migrator.connect() as conn:
                cfg = Config(str(ROOT / "alembic.ini"))
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            with migrator.begin() as conn:
                conn.execute(
                    text(
                        'GRANT SELECT,INSERT,DELETE ON smartregression.web_reporting_views TO "'
                        + name
                        + '"'
                    )
                )
                conn.execute(text('GRANT USAGE ON SCHEMA smartregression TO "' + name + '"'))
                conn.execute(
                    text(
                        "GRANT SELECT,INSERT,UPDATE ON smartregression.web_users,"
                        "smartregression.web_sessions,smartregression.web_account_tokens,"
                        "smartregression.web_rate_limits,smartregression.web_projects,"
                        "smartregression.web_runs,smartregression.web_ai_requests,"
                        'smartregression.web_notes,smartregression.web_view_states TO "'
                        + name
                        + '"'
                    )
                )
                conn.execute(
                    text(
                        "GRANT SELECT,INSERT ON smartregression.web_activity,"
                        "smartregression.repositories,smartregression.snapshots,"
                        "smartregression.analysis_runs,smartregression.artifacts,"
                        "smartregression.run_reports,smartregression.evidence_bundles,"
                        "smartregression.run_stage_payloads,smartregression.web_explorer_snapshots,"
                        'smartregression.web_scenarios TO "' + name + '"'
                    )
                )
                conn.execute(
                    text(
                        "GRANT SELECT ON smartregression.web_ai_campaigns,"
                        'smartregression.web_ai_grants TO "' + name + '"'
                    )
                )
            engine = stack.enter_context(
                database_engine(DatabaseSettings(runtime, allow_loopback_test=True))
            )
            inbox = Inbox()
            smtp = Controller(inbox, hostname="127.0.0.1", port=8151)
            smtp.start()

            @contextmanager
            def factory(url):
                if url != "https://github.com/owner/repo":
                    raise ValueError("synthetic_repository_only")
                value = remote(source)
                original = value._json

                def complete_tree(path):
                    result = original(path)
                    if "/git/trees/" in path:
                        result["tree"].append(
                            {"path": "src", "type": "tree", "mode": "040000", "sha": "f" * 40}
                        )
                    return result

                value._json = complete_tree
                yield value

            def publish(execution, repository):
                report = execution.report
                persist_report(
                    ReportFiles(artifacts, source_repository=repository),
                    PostgresAnalysisStore(engine, report),
                    report=report,
                    configuration=execution.configuration,
                    snapshot_manifests=execution.snapshot_manifests,
                    artifact_id=report.report_id,
                    storage_key=f"{report.identity.run_id}/{report.report_id}.json",
                    bundle=bundle_from_report(report),
                )

            repository = RepositoryService(factory, None, publisher=publish)
            auth = AuthService(PostgresAuthStore(engine), PasswordHasher(), TestSmtp(), token_hash)
            projects = ProjectService(
                PostgresProjectStore(engine), repository.inspect, repository.tree
            )
            runs = WebRunService(PostgresWebRunStore(engine), repository.analyze)
            explorer = ExplorerService(PostgresExplorerStore(engine), factory, parse_javascript)
            notes = NoteService(PostgresNoteStore(engine))
            scenarios = ScenarioService(PostgresScenarioStore(engine), explorer)
            ai = WebAiService(
                PostgresAiStore(engine),
                runs.store.report,
                lambda *args: NarrativeResult(status="failed", error_code="provider_configuration"),
            )
            app = create_app(
                auth_service=auth,
                auth_settings=AuthSettings(
                    ORIGIN, b"e2e-synthetic-secret-not-production" * 2, ORIGIN.startswith("http:")
                ),
                project_service=projects,
                web_run_service=runs,
                explorer_service=explorer,
                note_service=notes,
                scenario_service=scenarios,
                web_ai_service=ai,
                reporting_service=__import__(
                    "smartregression.composition", fromlist=["product_reporting_service"]
                ).product_reporting_service(auth),
                mode="product",
            )

            @app.get("/__test__/mail")
            def mail(request: Request, email: str):
                if request.headers.get("x-test-inbox") != "synthetic-e2e-only" or not re.fullmatch(
                    r"[a-z0-9_-]+@example.com", email
                ):
                    return JSONResponse(status_code=404, content={})
                return {"messages": [m for m in inbox.messages if m["to"] == email]}

            app.mount(
                "/assets", StaticFiles(directory=ROOT / "frontend/dist/assets"), name="assets"
            )

            @app.get("/{path:path}")
            def frontend(path: str):
                if path.startswith(("api/", "__test__/")):
                    return JSONResponse(status_code=404, content={"code": "not_found"})
                return FileResponse(ROOT / "frontend/dist/index.html")

            (ROOT / "var/phase3-8/e2e-ready.json").write_text(
                json.dumps(
                    {
                        "origin": ORIGIN,
                        "scope": "synthetic GitHub; real PostgreSQL and SMTP; disposable DB",
                        "artifact_root": str(root),
                    }
                )
            )
            server = uvicorn.Server(
                uvicorn.Config(
                    app,
                    host="127.0.0.1",
                    port=8150,
                    access_log=False,
                    proxy_headers=False,
                )
            )

            @app.post("/__test__/stop")
            def stop(request: Request):
                if request.headers.get("x-test-inbox") != "synthetic-e2e-only":
                    return JSONResponse(status_code=404, content={})
                server.should_exit = True
                return {"stopping": True}

            server.run()
    finally:
        if smtp:
            smtp.stop()
        if created:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))
        admin.close()


if __name__ == "__main__":
    main()

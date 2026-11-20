"""Real browser -> Vite proxy -> product HTTP -> PostgreSQL and static parser.

Opt-in native campaign. Only GitHub transport and email delivery are fixtures.
No route interception, paid AI, account database or external email is used.
"""

import json
import os
import secrets
import socket
import subprocess
import threading
import time
from pathlib import Path
from urllib.request import urlopen

import pytest
import uvicorn
from backend.tests.integration.storage.test_auth import accounts  # noqa: F401
from backend.tests.integration.storage.test_explorer import explorer  # noqa: F401
from backend.tests.integration.storage.test_web_runs import runs  # noqa: F401

from smartregression.adapters.storage.note_store import PostgresNoteStore
from smartregression.adapters.storage.scenario_store import PostgresScenarioStore
from smartregression.adapters.storage.web_ai_store import PostgresAiStore
from smartregression.adapters.storage.web_reporting import PostgresWebReporting
from smartregression.api.main import create_app
from smartregression.application.notes import NoteService
from smartregression.application.projects import ProjectService
from smartregression.application.repository_analysis import RepositoryService
from smartregression.application.scenarios import ScenarioService
from smartregression.application.web_ai import WebAiService
from smartregression.application.web_reporting import WebReportingService
from smartregression.auth_config import AuthSettings

ROOT = Path(__file__).resolve().parents[4]


def port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def ready(url, process=None):
    until = time.monotonic() + 30
    while time.monotonic() < until:
        if process and process.poll() is not None:
            pytest.fail("owned_frontend_exited")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    pytest.fail("owned_service_start_timeout")


def test_real_browser_signup_to_export_and_restart(request):
    account_fixture = request.getfixturevalue("accounts")
    snapshot_fixture = request.getfixturevalue("explorer")
    run_fixture = request.getfixturevalue("runs")
    node = os.environ.get("SMARTREGRESSION_TEST_NODE")
    if not node or not Path(node).is_file():
        pytest.skip("set SMARTREGRESSION_TEST_NODE to installed Node 22 executable")
    folder = ROOT / "var/tasks-352-360" / ("browser-" + secrets.token_hex(5))
    folder.mkdir(parents=True)
    backend_port, frontend_port = port(), port()
    origin = f"http://127.0.0.1:{frontend_port}"
    auth, mailbox, *_ = account_fixture
    engine = run_fixture[0].store.engine
    discovery = RepositoryService(snapshot_fixture[0].source_factory, None)
    projects = ProjectService(run_fixture[4].store, discovery.inspect, discovery.tree)
    notes = NoteService(PostgresNoteStore(engine))
    scenarios = ScenarioService(PostgresScenarioStore(engine), snapshot_fixture[0])
    calls = []

    def forbidden_provider(*args):
        calls.append(True)
        raise AssertionError("provider_must_not_run")

    ai = WebAiService(PostgresAiStore(engine), run_fixture[0].store.report, forbidden_provider)
    settings = AuthSettings(origin, secrets.token_bytes(32), local_http=True)

    def app():
        return create_app(
            mode="product",
            auth_service=auth,
            auth_settings=settings,
            project_service=projects,
            web_run_service=run_fixture[0],
            web_ai_service=ai,
            explorer_service=snapshot_fixture[0],
            note_service=notes,
            scenario_service=scenarios,
            reporting_service=WebReportingService(PostgresWebReporting(engine)),
        )

    server = None
    thread = None

    def start():
        nonlocal server, thread
        server = uvicorn.Server(
            uvicorn.Config(
                app(),
                host="127.0.0.1",
                port=backend_port,
                log_level="error",
                access_log=False,
            )
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        ready(f"http://127.0.0.1:{backend_port}/api/v1/capabilities")

    def stop():
        if server:
            server.should_exit = True
            thread.join(timeout=15)
            assert not thread.is_alive(), "owned_backend_stop_timeout"

    # Config lives under frontend so Vite resolves the existing plugin dependencies.
    config = ROOT / "frontend" / ("vite.acceptance-" + secrets.token_hex(5) + ".mjs")
    config.write_text(
        'import base from "./vite.config.ts";\n'
        f'export default {{...base, server: {{host:"127.0.0.1",port:{frontend_port},'
        'strictPort:true,proxy:{"/api":{'
        f'target:"http://127.0.0.1:{backend_port}"'
        "}}}};\n",
        encoding="utf-8",
    )
    frontend = driver = None
    mailbox_file = folder / "synthetic-mailbox.json"
    old_send = mailbox.send

    def capture(email, purpose, token):
        old_send(email, purpose, token)
        # Synthetic one-use verification only; removed on exit, never logged.
        temp = mailbox_file.with_suffix(".tmp")
        temp.write_text(json.dumps(mailbox.messages), encoding="utf-8")
        temp.replace(mailbox_file)

    mailbox.send = capture
    try:
        start()
        with (
            (folder / "frontend.log").open("w", encoding="utf-8") as front_log,
            (folder / "browser.log").open("w", encoding="utf-8") as driver_log,
        ):
            frontend = subprocess.Popen(
                [node, "node_modules/vite/bin/vite.js", "--config", config.name],
                cwd=ROOT / "frontend",
                stdout=front_log,
                stderr=subprocess.STDOUT,
            )
            ready(origin, frontend)
            env = dict(
                os.environ,
                SMARTREGRESSION_ACCEPTANCE_ORIGIN=origin,
                SMARTREGRESSION_ACCEPTANCE_DIR=str(folder),
            )
            driver = subprocess.Popen(
                [node, "scripts/e2e-an-remaining.mjs"],
                cwd=ROOT / "frontend",
                env=env,
                stdout=driver_log,
                stderr=subprocess.STDOUT,
            )
            deadline = time.monotonic() + 210
            while driver.poll() is None and time.monotonic() < deadline:
                if (folder / "restart-request").exists():
                    (folder / "restart-request").unlink()
                    stop()
                    start()
                    (folder / "restart-done").touch()
                time.sleep(0.1)
            assert driver.poll() == 0, "browser_campaign_failed: inspect ignored browser.log"
        assert not calls
        result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        assert result["dashboard_runs"] == result["csv_rows"] == 1
        assert result["restart_resume"] and result["cross_owner_blocked"]
    finally:
        for process in (driver, frontend):
            if process and process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
        stop()
        mailbox.send = old_send
        mailbox_file.unlink(missing_ok=True)
        config.unlink(missing_ok=True)

"""One idempotent acceptance request; <=3 admitted calls / USD .06 per campaign.

Uses the configured verified account and a public cached snapshot. No key, email,
prompt or driver diagnostic is printed. Only confirmed 503 responses have bounded,
separately admitted retries. Replaying a completed request makes no generation.
"""

import argparse
import json
import subprocess
from contextlib import ExitStack
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine
from smartregression.auth_config import web_environment
from smartregression.composition import (
    account_service,
    personal_project_service,
    product_ai_service,
    product_explorer_service,
    product_repo_assistant_service,
)
from smartregression.contracts.repo_assistant import MessageCreate, ThreadCreate
from smartregression.core.explorer.graph import PARSER_CONFIG
from smartregression.gemini_config import GeminiCredential, credential_environment

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = "repo-assistant-acceptance-20261119"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sole-local-account", action="store_true")
    parser.add_argument("--attempt", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument("--recovery-check", action="store_true")
    parser.add_argument("--allow-fallback", action="store_true")
    options = parser.parse_args()
    campaign = "repo-assistant-recovery-20261119" if options.recovery_check else CAMPAIGN
    directory = ROOT / (
        "var/assistant-recovery-20261119"
        if options.recovery_check
        else "var/assistant-acceptance-20261119"
    )
    env = web_environment()
    key_file = env.get("SMARTREGRESSION_GEMINI_ENV_FILE")
    credential = GeminiCredential.from_environment(
        credential_environment(Path(key_file) if key_file else None)
    )
    context = json.loads((ROOT / "var/auth/local-context.json").read_text())
    info = json.loads(
        subprocess.check_output(["docker", "inspect", context["container_id"]], timeout=15)
    )[0]
    url = make_url(env["SMARTREGRESSION_MIGRATION_DATABASE_URL"])
    if (
        info["Config"]["Labels"].get("smartregression.auth-local") != context["nonce"]
        or info["NetworkSettings"]["Ports"]["5432/tcp"]
        != [{"HostIp": "127.0.0.1", "HostPort": str(url.port)}]
        or url.host != "127.0.0.1"
        or url.database != "smartregression_auth_local"
        or url.username != "postgres"
    ):
        raise ValueError("owned_database_required")
    with ExitStack() as stack:
        if options.diagnose:
            from unittest.mock import patch

            from smartregression.adapters.llm.repository_summary import GeminiRepositoryNarrator
            from smartregression.core.retrieval.exclusions import contains_recognized_secret

            def record_diagnostic(value):
                result = dict(value)
                result["message"] = result["message"].replace(credential.api_key, "[REDACTED]")[
                    :1000
                ]
                if contains_recognized_secret(result["message"]):
                    result["message"] = "[REDACTED]"
                directory.mkdir(parents=True, exist_ok=True)
                index = (
                    len(list(directory.glob(f"diagnostic-attempt-{options.attempt}-event-*.json")))
                    + 1
                )
                (directory / f"diagnostic-attempt-{options.attempt}-event-{index}.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
                )

            stack.enter_context(
                patch(
                    "smartregression.adapters.llm.repository_summary.GeminiRepositoryNarrator",
                    side_effect=lambda provider, ledger: GeminiRepositoryNarrator(
                        provider, ledger, diagnostic=record_diagnostic
                    ),
                )
            )
        migrator = stack.enter_context(
            database_engine(DatabaseSettings(url, allow_loopback_test=True))
        )
        with migrator.begin() as conn:
            conn.execute(text("SELECT pg_advisory_xact_lock(741031)"))
            if options.sole_local_account:
                owners = (
                    conn.execute(
                        text(
                            "SELECT id FROM smartregression.web_users "
                            "WHERE verified AND enabled FOR UPDATE"
                        )
                    )
                    .scalars()
                    .all()
                )
                if len(owners) != 1:
                    raise ValueError("single_verified_local_account_required")
                owner = owners[0]
            else:
                owner = conn.execute(
                    text(
                        "SELECT id FROM smartregression.web_users WHERE email=:email "
                        "AND verified AND enabled FOR UPDATE"
                    ),
                    {"email": env["SMARTREGRESSION_SMTP_USERNAME"].strip().lower()},
                ).scalar_one()
            conn.execute(
                text(
                    "INSERT INTO smartregression.web_ai_campaigns(id,max_calls,cap_micro_usd) "
                    "VALUES(:id,3,60000) ON CONFLICT(id) DO NOTHING"
                ),
                {"id": campaign},
            )
            limits = conn.execute(
                text(
                    "SELECT max_calls,cap_micro_usd FROM smartregression.web_ai_campaigns "
                    "WHERE id=:id"
                ),
                {"id": campaign},
            ).one()
            if tuple(limits) != (3, 60000):
                raise ValueError("campaign_mismatch")
            conn.execute(
                text(
                    "INSERT INTO smartregression.web_ai_grants"
                    "(campaign_id,owner_id,max_calls,cap_micro_usd) "
                    "VALUES(:id,:owner,3,60000) ON CONFLICT(campaign_id,owner_id) DO NOTHING"
                ),
                {"id": campaign, "owner": owner},
            )
            snapshot = conn.execute(
                text(
                    "SELECT s.project_id,s.commit FROM smartregression.web_explorer_snapshots s "
                    "JOIN smartregression.web_projects p ON p.id=s.project_id "
                    "AND p.owner_id=s.owner_id "
                    "WHERE s.owner_id=:owner AND s.config_digest=:config AND NOT p.archived "
                    "ORDER BY s.created_at DESC LIMIT 1"
                ),
                {"owner": owner, "config": PARSER_CONFIG},
            ).first()
            if snapshot is None:
                raise ValueError("no_owned_snapshot_available")
        auth, _ = account_service(stack, required=True)
        projects = personal_project_service(auth)
        explorer = product_explorer_service(auth)
        from smartregression.adapters.storage.web_run_store import PostgresWebRunStore
        from smartregression.application.web_runs import WebRunService

        ai = product_ai_service(
            auth, WebRunService(PostgresWebRunStore(auth.store.engine), None), recover=False
        )
        assistant = product_repo_assistant_service(auth, explorer, projects, ai)
        owner, project = str(owner), str(snapshot.project_id)
        thread = assistant.create_thread(
            owner,
            project,
            ThreadCreate(
                commit=snapshot.commit,
                title="Kiểm chứng Gemini 3.8 Flash",
                idempotency_key=campaign,
            ),
        )
        body = MessageCreate(
            question="Giải thích cấu trúc repository và gợi ý thứ tự đọc "
            "từ bằng chứng đã cung cấp. Nêu rõ điều chưa xác định.",
            action="overview",
            idempotency_key=f"flash38-overview-{options.attempt}",
            use_llm=True,
            allow_metadata_egress=True,
            allow_model_fallback=options.allow_fallback,
        )
        message, execution = assistant.send(owner, project, str(thread.id), body)
        if execution:
            assistant.execute_ai(*execution)
        message = next(
            m for m in assistant.messages(owner, project, str(thread.id)) if m.id == message.id
        )
        directory.mkdir(parents=True, exist_ok=True)
        output = directory / f"result-attempt-{options.attempt}.json"
        output.write_text(message.model_dump_json(indent=2), encoding="utf-8")
        result = message.ai.result
        print(
            json.dumps(
                {
                    "status": message.ai.status,
                    "model": result.model if result else None,
                    "error_code": result.error_code if result else None,
                    "evidence": str(output),
                    "actual_cost_usd": None,
                    "campaign_max_calls": 3,
                    "campaign_cap_usd": 0.06,
                }
            )
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "not_completed", "failure_type": type(error).__name__}))
        raise SystemExit(1) from None

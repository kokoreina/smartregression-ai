"""Explicit six-action live smoke against public sqlparse, under existing grant.

No account password, token, prompt or key is printed. Never retries generation;
idempotency keys persist across invocations. A failed/uncertain attempt remains used.
"""

import argparse
import json
from contextlib import ExitStack
from pathlib import Path

from sqlalchemy import text

from smartregression.adapters.storage.web_run_store import PostgresWebRunStore
from smartregression.application.assistance_ai import AssistanceAiService
from smartregression.application.web_runs import WebRunService
from smartregression.auth_config import web_environment
from smartregression.composition import (
    account_service,
    personal_project_service,
    product_ai_service,
    product_explorer_service,
    product_scenario_service,
)
from smartregression.contracts.ai_requests import AssistanceAiRequest
from smartregression.contracts.projects import ProjectCreate
from smartregression.contracts.scenarios import ScenarioCreate
from smartregression.contracts.web_runs import AiRequest, RunCreate

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = "sprint3-acceptance-20261115"
TARGET = "be3b7a68d07af5a22b49765e26d2541be640999f"
BASE = "91149dffdf691945dc5e20d9c9623390d9b96ffb"
REPO = "https://github.com/andialbrecht/sqlparse"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-fix", action="store_true")
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--folder-schema-fix", action="store_true")
    options = parser.parse_args()
    directory = ROOT / "var/phase3-8/live-ai"
    if any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)):
        raise ValueError("unsafe_workspace")
    directory.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        auth, _ = account_service(stack, required=True)
        with auth.store.engine.begin() as conn:
            owner = conn.execute(
                text(
                    "SELECT id FROM smartregression.web_users "
                    "WHERE email=:email AND verified AND enabled"
                ),
                {"email": web_environment()["SMARTREGRESSION_SMTP_USERNAME"].strip().lower()},
            ).scalar_one()
            grant = conn.execute(
                text(
                    "SELECT max_calls,cap_micro_usd FROM smartregression.web_ai_grants "
                    "WHERE owner_id=:owner AND campaign_id=:campaign"
                ),
                {"owner": owner, "campaign": CAMPAIGN},
            ).one()
            if grant != (10, 200000):
                raise ValueError("explicit_acceptance_grant_required")
            campaign_ids = (
                conn.execute(
                    text(
                        "SELECT campaign_id FROM smartregression.web_ai_grants "
                        "WHERE owner_id=:owner"
                    ),
                    {"owner": owner},
                )
                .scalars()
                .all()
            )
            if campaign_ids != [CAMPAIGN]:
                raise ValueError("single_acceptance_campaign_required")
        owner = str(owner)
        projects = personal_project_service(auth)
        existing = [p for p in projects.list(owner).items if p.repository_url == REPO]
        project = (
            existing[0]
            if existing
            else projects.create(
                owner, ProjectCreate(title="DEMO · Sprint 3 AI acceptance", repository_url=REPO)
            )
        )
        identity = str(project.id)
        explorer = product_explorer_service(auth)
        snapshot = explorer.materialize(owner, identity, TARGET)
        from smartregression.composition import published_repository_service

        runs = WebRunService(
            PostgresWebRunStore(auth.store.engine), published_repository_service(auth).analyze
        )
        ai = product_ai_service(auth, runs, recover=False)
        scenarios = product_scenario_service(auth, explorer)
        scoped = AssistanceAiService(ai.store, explorer, scenarios, ai.explain)
        path = "sqlparse/engine/grouping.py"
        if path not in snapshot.graph.coverage.analyzed_files:
            path = snapshot.graph.coverage.analyzed_files[0]
        hypothesis = scenarios.create(
            owner,
            identity,
            ScenarioCreate(
                baseline=TARGET,
                path=path,
                title="DEMO · Thêm bước kiểm tra đầu vào",
                mode="description",
                input=(
                    "Giả sử bổ sung kiểm tra đầu vào tại file này. "
                    "Giải thích các quan hệ quan sát được cần đọc lại, "
                    "tách rõ giả định khỏi bằng chứng tĩnh."
                ),
                idempotency_key="acceptance-hypothesis-20261115",
            ),
        )
        outcomes = []
        saved = [
            run
            for run in runs.store.list(owner, identity).items
            if run.base == BASE and run.target == TARGET and run.report_available
        ]
        if options.export_only:
            from smartregression.application.web_exports import WebExportService

            exports = WebExportService(runs, scenarios, ai)
            if not saved:
                raise ValueError("saved_live_report_required")
            (directory / "sqlparse-run.json").write_text(
                exports.run(owner, identity, str(saved[0].id)).model_dump_json(indent=2),
                encoding="utf-8",
            )
            (directory / "sqlparse-hypothesis.json").write_text(
                exports.scenario(owner, identity, str(hypothesis.id)).model_dump_json(indent=2),
                encoding="utf-8",
            )
            print(
                json.dumps({"exported": True, "provider_calls": 0, "artifact_root": str(directory)})
            )
            return
        if not saved:
            run, _ = runs.create(
                owner,
                identity,
                RunCreate(base=BASE, target=TARGET, idempotency_key="acceptance-static-20261115"),
            )
            if run.status == "queued":
                runs.execute(owner, identity, str(run.id))
            run = runs.store.get(owner, identity, str(run.id))
            if run.report_available:
                saved = [run]
        if saved:
            body = AiRequest(
                idempotency_key="acceptance-commit-20261115", allow_metadata_egress=True
            )
            job, created, batch, campaign = ai.create(owner, identity, str(saved[0].id), body)
            if created:
                ai.execute(
                    owner, identity, str(saved[0].id), str(job.id), batch, campaign, body.question
                )
            job = ai.store.get(owner, identity, str(saved[0].id), str(job.id))
            (directory / "commit.json").write_text(job.model_dump_json(indent=2), encoding="utf-8")
            outcomes.append(
                {
                    "action": "commit",
                    "status": job.status,
                    "error_code": job.result.error_code if job.result else None,
                }
            )
        else:
            outcomes.append(
                {
                    "action": "commit",
                    "status": "pending",
                    "reason": "No matching saved canonical run yet; no automatic duplicate run.",
                }
            )
        actions = [
            (
                "hypothesis",
                path,
                str(hypothesis.id),
                "Giải thích giả thuyết bằng bằng chứng đã cung cấp.",
            ),
            ("reading_guide", None, None, "Đề xuất thứ tự đọc từ cấu trúc quan sát được."),
            ("search", None, None, "grouping"),
            (
                "file",
                "sqlparse/__init__.py",
                None,
                "Giải thích vai trò file trong phạm vi quan sát.",
            ),
            (
                "folder",
                "sqlparse/engine",
                None,
                "Tóm tắt thư mục từ các file được cung cấp, nêu phần bỏ qua.",
            ),
        ]
        for action, path, scenario_id, question in actions:
            try:
                if options.folder_schema_fix and action != "folder":
                    saved_path = directory / (
                        action
                        + ("-context-v2" if action in {"file", "hypothesis"} else "")
                        + ".json"
                    )
                    from smartregression.contracts.ai_requests import AiJob

                    previous = AiJob.model_validate_json(saved_path.read_text("utf-8"))
                    outcomes.append(
                        {
                            "action": action,
                            "status": previous.status,
                            "error_code": previous.result.error_code if previous.result else None,
                            "reused_saved_attempt": True,
                        }
                    )
                    continue
                suffix = ""
                original_file = directory / (action + ".json")
                if options.context_fix and original_file.exists():
                    from smartregression.contracts.ai_requests import AiJob

                    original = AiJob.model_validate_json(original_file.read_text("utf-8"))
                    if original.status == "failed":
                        ledger_path = (
                            ROOT
                            / "var/web-ai"
                            / CAMPAIGN
                            / ("batch-1.json" if action != "folder" else "batch-2.json")
                        )
                        ledger = json.loads(ledger_path.read_text("utf-8"))
                        record = next(
                            (r for r in ledger["runs"] if r["id"] == str(original.id)), None
                        )
                        if record is None or any(
                            e["kind"] == "generation" for e in record["entries"]
                        ):
                            raise ValueError("uncertain_generation_must_not_be_retried")
                        suffix = "-context-v2"
                if options.folder_schema_fix:
                    suffix = "-schema-v3"
                old_file = directory / (action + suffix + ".json")
                if old_file.exists():
                    from smartregression.contracts.ai_requests import AiJob

                    old = AiJob.model_validate_json(old_file.read_text("utf-8"))
                    checked = ai.store.scoped_get(owner, identity, str(old.id))
                    if checked.action != action or checked.provenance.get("commit") != TARGET:
                        raise ValueError("saved_acceptance_scope_mismatch")
                    outcomes.append(
                        {
                            "action": action,
                            "status": checked.status,
                            "error_code": checked.result.error_code if checked.result else None,
                            "reused_saved_attempt": True,
                        }
                    )
                    continue
                body = AssistanceAiRequest(
                    commit=TARGET,
                    action=action,
                    path=path,
                    scenario_id=scenario_id,
                    question=question,
                    allow_metadata_egress=True,
                    idempotency_key="acceptance-" + action + "-20261115" + suffix,
                )
                job, created, batch, campaign, context = scoped.create(owner, identity, body)
                if campaign != CAMPAIGN:
                    raise ValueError("campaign_mismatch")
                if created:
                    scoped.execute(owner, str(job.id), batch, campaign, context)
                job = ai.store.scoped_get(owner, identity, str(job.id))
                (directory / (action + suffix + ".json")).write_text(
                    job.model_dump_json(indent=2), encoding="utf-8"
                )
                outcomes.append(
                    {
                        "action": action,
                        "status": job.status,
                        "error_code": job.result.error_code if job.result else None,
                    }
                )
                if job.result and job.result.error_code in {
                    "provider_quota",
                    "provider_configuration",
                }:
                    break
            except Exception as error:
                from smartregression.application.auth import AuthFailure

                outcomes.append(
                    {
                        "action": action,
                        "status": "pending",
                        "error_code": error.code
                        if isinstance(error, AuthFailure)
                        else "acceptance_precondition_failed",
                    }
                )
        quota = ai.store.quota(owner)
        from smartregression.application.web_exports import WebExportService

        exports = WebExportService(runs, scenarios, ai)
        if saved:
            (directory / "sqlparse-run.json").write_text(
                exports.run(owner, identity, str(saved[0].id)).model_dump_json(indent=2),
                encoding="utf-8",
            )
        (directory / "sqlparse-hypothesis.json").write_text(
            exports.scenario(owner, identity, str(hypothesis.id)).model_dump_json(indent=2),
            encoding="utf-8",
        )
        result = {
            "scope": "live Gemini; public sqlparse metadata only; not a quality benchmark",
            "campaign": CAMPAIGN,
            "outcomes": outcomes,
            "quota": quota.model_dump(),
            "generations_not_retried": True,
        }
        (directory / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit(
            "Live acceptance stopped; private details withheld; inspect sanitized evidence."
        ) from None

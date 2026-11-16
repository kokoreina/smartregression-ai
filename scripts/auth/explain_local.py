"""Record EXPLAIN plan structure only, without owner IDs, SQL values or source."""

import json

from owned_database import ROOT, owned_database
from sqlalchemy import text

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine
from smartregression.adapters.storage.retention import prune_cache


def summarize(plan):
    return {
        "node_type": plan["Node Type"],
        "index_name": plan.get("Index Name"),
        "estimated_rows": plan.get("Plan Rows"),
        "children": [summarize(p) for p in plan.get("Plans", [])],
    }


def main():
    url, _ = owned_database()
    plans = {}
    with database_engine(DatabaseSettings(url, allow_loopback_test=True)) as engine:
        with engine.connect() as conn:
            pair = conn.execute(
                text("SELECT owner_id,id FROM smartregression.web_projects ORDER BY id LIMIT 1")
            ).first()
            if pair is None:
                raise ValueError("project_fixture_required")
            for name, query in {
                "run_history": (
                    "SELECT id FROM smartregression.web_runs "
                    "WHERE owner_id=:owner AND project_id=:project "
                    "ORDER BY started_at DESC,id DESC LIMIT 25"
                ),
                "activity": (
                    "SELECT id FROM smartregression.web_activity "
                    "WHERE owner_id=:owner AND project_id=:project "
                    "ORDER BY created_at DESC,id DESC LIMIT 25"
                ),
                "notes": (
                    "SELECT id FROM smartregression.web_notes "
                    "WHERE owner_id=:owner AND project_id=:project "
                    "ORDER BY created_at DESC,id DESC LIMIT 25"
                ),
            }.items():
                plan = conn.execute(
                    text("EXPLAIN(FORMAT JSON) " + query), {"owner": pair[0], "project": pair[1]}
                ).scalar_one()
                plans[name] = summarize(plan[0]["Plan"])
        result = {
            "scope": "owned development DB; EXPLAIN estimates only, not production latency",
            "plans": plans,
            "retention_dry_run": prune_cache(engine),
        }
    path = ROOT / "var/phase3-8/query-plans.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"recorded": True, "artifact": str(path)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Query plan check failed; private details withheld.") from None

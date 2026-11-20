"""Operator-only cache retention. Business reports, notes and archived projects stay."""

from datetime import UTC, datetime, timedelta

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.project_store import BoundProjectStore

SNAPSHOTS = """
SELECT s.owner_id,s.project_id,s.commit,s.config_digest
FROM smartregression.web_explorer_snapshots s
WHERE s.created_at<:cutoff
AND NOT EXISTS (SELECT 1 FROM smartregression.web_notes n
    WHERE n.owner_id=s.owner_id AND n.project_id=s.project_id AND n.commit=s.commit)
AND NOT EXISTS (SELECT 1 FROM smartregression.web_scenarios c
    WHERE c.owner_id=s.owner_id AND c.project_id=s.project_id
    AND c.baseline=s.commit AND c.config_digest=s.config_digest)
AND NOT EXISTS (SELECT 1 FROM smartregression.web_runs r
    WHERE r.owner_id=s.owner_id AND r.project_id=s.project_id
    AND (r.base=s.commit OR r.target=s.commit))
AND NOT EXISTS (SELECT 1 FROM smartregression.web_ai_requests a
    WHERE a.owner_id=s.owner_id AND a.project_id=s.project_id
    AND a.snapshot_commit=s.commit AND a.snapshot_config=s.config_digest)
AND NOT EXISTS (SELECT 1 FROM smartregression.web_view_states v
    WHERE v.owner_id=s.owner_id AND v.project_id=s.project_id AND v.commit=s.commit
    AND v.updated_at>=:cutoff)
AND NOT EXISTS (SELECT 1 FROM smartregression.web_assistant_threads t
    WHERE t.owner_id=s.owner_id AND t.project_id=s.project_id
    AND t.commit=s.commit AND t.config_digest=s.config_digest)
AND NOT EXISTS (SELECT 1 FROM smartregression.web_repo_watches w
    WHERE w.owner_id=s.owner_id AND w.project_id=s.project_id AND w.last_commit=s.commit)
AND NOT EXISTS (SELECT 1 FROM smartregression.web_change_notifications n
    WHERE n.owner_id=s.owner_id AND n.project_id=s.project_id
    AND (n.report->>'base'=s.commit OR n.report->>'target'=s.commit)
    AND n.report->>'config_digest'=s.config_digest)
"""


def prune_cache(
    engine, *, apply: bool = False, now: datetime | None = None
) -> dict[str, int | bool]:
    cutoff = (now or datetime.now(UTC)) - timedelta(days=90)
    with database_transaction(engine) as connection:
        tx = BoundProjectStore(connection)
        tx.execute("SELECT pg_advisory_xact_lock(741031)")
        states = tx.execute(
            "SELECT count(*) FROM smartregression.web_view_states WHERE updated_at<:cutoff",
            cutoff=cutoff,
        ).scalar_one()
        snapshots = tx.execute(
            "SELECT count(*) FROM (" + SNAPSHOTS + ") eligible", cutoff=cutoff
        ).scalar_one()
        if apply:
            tx.execute(
                "DELETE FROM smartregression.web_view_states WHERE updated_at<:cutoff",
                cutoff=cutoff,
            )
            tx.execute(
                "DELETE FROM smartregression.web_explorer_snapshots "
                "WHERE (owner_id,project_id,commit,config_digest) IN (" + SNAPSHOTS + ")",
                cutoff=cutoff,
            )
        return {"applied": apply, "view_states": states, "snapshots": snapshots}

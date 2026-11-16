"""One repeatable-read snapshot backs dashboard, drilldown and CSV export."""

from datetime import timedelta
from uuid import uuid4

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.explorer_store import digest, encoded
from smartregression.adapters.storage.project_store import BoundProjectStore
from smartregression.adapters.storage.web_run_store import PostgresWebRunStore
from smartregression.application.auth import AuthFailure
from smartregression.application.web_reporting import csv_text
from smartregression.contracts.web_reporting import Dashboard, UsagePage, UsageRecord
from smartregression.contracts.web_runs import RunPage, WebRun


class PostgresWebReporting:
    def __init__(self, engine):
        self.engine = engine

    def dashboard(self, owner, filters):
        identity = str(uuid4())
        params = {
            "owner": owner,
            "start": filters.start,
            "end": filters.end,
            "zone": filters.timezone,
        }
        predicate = "owner_id=:owner AND started_at>=:start AND started_at<:end"
        if filters.project_id:
            predicate += " AND project_id=:project"
            params["project"] = str(filters.project_id)
        if filters.status:
            predicate += " AND status=:status"
            params["status"] = filters.status
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            tx.lock_owner(owner)
            if filters.project_id:
                tx.get(owner, str(filters.project_id))
            # Bound cache footprint; immutable snapshots expire after 24 hours.
            tx.execute(
                "DELETE FROM smartregression.web_reporting_views WHERE owner_id=:owner "
                "AND (expires_at<CURRENT_TIMESTAMP OR id IN (SELECT id FROM "
                "smartregression.web_reporting_views WHERE owner_id=:owner "
                "ORDER BY created_at DESC,id DESC OFFSET 19))",
                owner=owner,
            )
            rows = (
                tx.execute(
                    "SELECT *,payload IS NOT NULL AS report_available "
                    "FROM smartregression.web_runs WHERE "
                    + predicate
                    + " ORDER BY started_at DESC,id DESC LIMIT 10001",
                    **params,
                )
                .mappings()
                .all()
            )
            statuses = dict(
                tx.execute(
                    "SELECT status,count(*) FROM smartregression.web_runs WHERE "
                    + predicate
                    + " GROUP BY status",
                    **params,
                ).all()
            )
            ai_statuses = dict(
                tx.execute(
                    "SELECT ai_status,count(*) FROM smartregression.web_runs WHERE "
                    + predicate
                    + " GROUP BY ai_status",
                    **params,
                ).all()
            )
            daily = dict(
                tx.execute(
                    "SELECT to_char(started_at AT TIME ZONE :zone,'YYYY-MM-DD'),count(*) "
                    "FROM smartregression.web_runs WHERE " + predicate + " GROUP BY 1 ORDER BY 1",
                    **params,
                ).all()
            )
            total = sum(statuses.values())
            ai_predicate = "a.owner_id=:owner AND a.created_at>=:start AND a.created_at<:end"
            if filters.project_id:
                ai_predicate += " AND a.project_id=:project"
            if filters.status:
                ai_predicate += (
                    " AND EXISTS(SELECT 1 FROM smartregression.web_runs r "
                    "WHERE r.id=a.run_id AND r.owner_id=a.owner_id AND r.status=:status)"
                )
            cost = (
                tx.execute(
                    "SELECT sum(actual_micro_usd) AS known,count(*) "
                    "FILTER(WHERE actual_micro_usd IS NULL) AS unknown,"
                    "coalesce(sum(reservation_micro_usd) FILTER(WHERE actual_micro_usd IS NULL),0) "
                    "AS reserved FROM smartregression.web_ai_requests a WHERE " + ai_predicate,
                    **params,
                )
                .mappings()
                .one()
            )
            usage_rows = (
                tx.execute(
                    "SELECT id,project_id,run_id,action,status,created_at,"
                    "reservation_micro_usd,actual_micro_usd "
                    "FROM smartregression.web_ai_requests a WHERE "
                    + ai_predicate
                    + " ORDER BY created_at DESC,id DESC LIMIT 10001",
                    **params,
                )
                .mappings()
                .all()
            )
            project_count = tx.execute(
                "SELECT count(DISTINCT project_id) FROM smartregression.web_runs WHERE "
                + predicate,
                **params,
            ).scalar_one()
            result = Dashboard(
                snapshot_id=identity,
                filters=filters,
                expires_at=filters.as_of + timedelta(hours=24),
                total_runs=total,
                project_count=project_count,
                static_statuses=statuses,
                ai_statuses=ai_statuses,
                daily_runs=daily,
                known_actual_micro_usd=cost["known"],
                unknown_actual_count=cost["unknown"],
                reservation_micro_usd=cost["reserved"],
                stored_rows=min(len(rows), 10000),
                limitations=[
                    "Runs are counted by started_at. AI requests are counted by created_at; "
                    "status filter excludes snapshot-only assistance.",
                    "Statuses and rows are frozen at the snapshot transaction; "
                    "refresh creates a new view.",
                    "Known provider usage is not an invoice; unknown cost remains unknown.",
                ]
                + (
                    ["More than 10,000 rows; narrow the filter to export all rows."]
                    if total > 10000
                    else []
                ),
            )
            payload = {
                "dashboard": result.model_dump(mode="json"),
                "rows": [
                    PostgresWebRunStore.view(row).model_dump(mode="json") for row in rows[:10000]
                ],
                "usage": [
                    UsageRecord.model_validate(dict(row)).model_dump(mode="json")
                    for row in usage_rows[:10000]
                ],
            }
            tx.execute(
                "INSERT INTO smartregression.web_reporting_views "
                "(id,owner_id,payload,payload_digest,expires_at) "
                "VALUES(:id,:owner,CAST(:payload AS jsonb),:digest,:expiry)",
                id=identity,
                owner=owner,
                payload=encoded(payload),
                digest=digest(payload),
                expiry=result.expires_at,
            )
            return result

    def read(self, owner, identity):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            row = (
                tx.execute(
                    "SELECT * FROM smartregression.web_reporting_views WHERE id=:id "
                    "AND owner_id=:owner AND expires_at>CURRENT_TIMESTAMP",
                    id=identity,
                    owner=owner,
                )
                .mappings()
                .first()
            )
            if row is None:
                raise AuthFailure("report_view_not_found", 404)
            if digest(row["payload"]) != row["payload_digest"]:
                raise AuthFailure("report_integrity_failed", 503)
            return row["payload"]

    def runs(self, owner, filters, cursor=None, limit=25):
        # Convenience for non-HTTP callers; API uses a specific immutable view id.
        view = self.dashboard(owner, filters)
        return self.page(owner, str(view.snapshot_id), int(cursor or 0), limit)

    def page(self, owner, identity, offset=0, limit=25):
        payload = self.read(owner, identity)
        rows = payload["rows"]
        return RunPage(
            items=[WebRun.model_validate(row) for row in rows[offset : offset + limit]],
            next_cursor=str(offset + limit) if offset + limit < len(rows) else None,
        )

    def csv(self, owner, filters):
        return self.export_csv(owner, str(self.dashboard(owner, filters).snapshot_id))

    def usage_page(self, owner, identity, offset=0, limit=25):
        rows = self.read(owner, identity)["usage"]
        return UsagePage(
            items=[UsageRecord.model_validate(row) for row in rows[offset : offset + limit]],
            next_cursor=str(offset + limit) if offset + limit < len(rows) else None,
        )

    def export_csv(self, owner, identity):
        payload = self.read(owner, identity)
        if payload["dashboard"]["total_runs"] > 10000:
            raise AuthFailure("export_row_limit", 422)
        rows = [
            [
                "run_id",
                "project_id",
                "repository_url",
                "base",
                "target",
                "static_status",
                "ai_status",
                "started_at",
                "finished_at",
                "as_of",
                "timezone",
            ]
        ]
        filters = payload["dashboard"]["filters"]
        for row in payload["rows"]:
            rows.append(
                [
                    row["id"],
                    row["project_id"],
                    row["repository_url"],
                    row["base"],
                    row["target"],
                    row["status"],
                    row["ai_status"],
                    row["started_at"],
                    row["finished_at"],
                    filters["as_of"],
                    filters["timezone"],
                ]
            )
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            for project in sorted({row["project_id"] for row in payload["rows"]}):
                tx.activity(owner, project, "export_generated", identity)
        return csv_text(rows)

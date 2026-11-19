"""PostgreSQL lifecycle/idempotency, linked immutable payloads, and owner-scoped reads."""

import hashlib
import json
from uuid import uuid4

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.project_store import BoundProjectStore
from smartregression.application.auth import AuthFailure
from smartregression.application.projects import decode_cursor
from smartregression.contracts.repository import RepositoryAnalysisResponse
from smartregression.contracts.web_runs import RunPage, SavedRunReport, WebRun


class PostgresWebRunStore:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def view(row):
        if row is None:
            raise AuthFailure("run_not_found", 404)
        return WebRun.model_validate(
            {key: row[key] for key in WebRun.model_fields if key != "schema_version"}
        )

    @staticmethod
    def row(tx, owner, project, identity):
        return (
            tx.execute(
                "SELECT *,payload IS NOT NULL AS report_available FROM smartregression.web_runs "
                "WHERE owner_id=:owner AND project_id=:project AND id=:id",
                owner=owner,
                project=project,
                id=identity,
            )
            .mappings()
            .first()
        )

    def claim(self, owner, project, body, config):
        digest = hashlib.sha256(
            json.dumps(
                {"base": body.base, "target": body.target, "config": config}, sort_keys=True
            ).encode()
        ).hexdigest()
        with database_transaction(self.engine) as connection:
            tx = BoundProjectStore(connection)
            # One globally ordered lock protects the two-slot bound across accounts/workers.
            tx.execute("SELECT pg_advisory_xact_lock(741031)")
            tx.lock_owner(owner)
            current = tx.get(owner, project, lock=True)
            old = (
                tx.execute(
                    "SELECT *,payload IS NOT NULL AS report_available FROM smartregres"
                    "sion.web_runs "
                    "WHERE owner_id=:owner AND project_id=:project AND idempotency_key=:key",
                    owner=owner,
                    project=project,
                    key=body.idempotency_key,
                )
                .mappings()
                .first()
            )
            if old:
                if old["request_digest"] != digest:
                    raise AuthFailure("idempotency_conflict", 409)
                return self.view(old), False
            if current.archived:
                raise AuthFailure("project_archived", 409)
            active = (
                tx.execute(
                    "SELECT owner_id FROM smartregression.web_runs WHERE status "
                    "IN ('queued','running') "
                    "UNION ALL SELECT owner_id FROM smartregression.web_ai_requests "
                    "WHERE status IN ('queued','running')"
                )
                .scalars()
                .all()
            )
            if owner in {str(value) for value in active} or len(active) >= 2:
                raise AuthFailure("analysis_busy", 409)
            identity = str(uuid4())
            row = (
                tx.execute(
                    "INSERT INTO smartregression.web_runs "
                    "(id,owner_id,project_id,repository_url,base,target,config_digest,"
                    "idempotency_key,request_digest,status) "
                    "VALUES(:id,:owner,:project,:url,:base,:target,:config,:key,:digest,'queued') "
                    "RETURNING *,FALSE AS report_available",
                    id=identity,
                    owner=owner,
                    project=project,
                    url=current.repository_url,
                    base=body.base,
                    target=body.target,
                    config=config,
                    key=body.idempotency_key,
                    digest=digest,
                )
                .mappings()
                .one()
            )
            tx.activity(owner, project, "run_created", identity)
            return self.view(row), True

    def get(self, owner, project, identity):
        with database_transaction(self.engine) as connection:
            tx = BoundProjectStore(connection)
            tx.get(owner, project)
            return self.view(self.row(tx, owner, project, identity))

    def start(self, owner, project, identity):
        with database_transaction(self.engine) as connection:
            tx = BoundProjectStore(connection)
            tx.lock_owner(owner)
            current = tx.get(owner, project)
            if current.archived:
                self._finish(tx, owner, project, identity, "project_archived")
                return False
            return (
                tx.execute(
                    "UPDATE smartregression.web_runs SET status='running' "
                    "WHERE owner_id=:owner AND project_id=:project AND id=:id AND stat"
                    "us='queued' RETURNING id",
                    owner=owner,
                    project=project,
                    id=identity,
                ).first()
                is not None
            )

    def list(self, owner, project, cursor=None, limit=25, *, status=None):
        decoded = decode_cursor(cursor)
        params = dict(owner=owner, project=project, limit=limit + 1)
        clause = ""
        if status is not None:
            if status not in {"queued", "running", "completed", "failed", "interrupted"}:
                raise AuthFailure("invalid_run_status", 422)
            clause += " AND status=:status"
            params["status"] = status
        if decoded:
            clause += " AND (started_at,id)<(:stamp,CAST(:cursor_id AS uuid))"
            params.update(stamp=decoded[0], cursor_id=decoded[1])
        with database_transaction(self.engine) as connection:
            tx = BoundProjectStore(connection)
            tx.get(owner, project)
            rows = (
                tx.execute(
                    "SELECT *,payload IS NOT NULL AS report_available FROM smartregres"
                    "sion.web_runs "
                    "WHERE owner_id=:owner AND project_id=:project"
                    + clause
                    + " ORDER BY started_at DESC,id DESC LIMIT :limit",
                    **params,
                )
                .mappings()
                .all()
            )
            items = [self.view(row) for row in rows]
        next_cursor = None
        if len(items) > limit:
            import base64

            last = items[limit - 1]
            next_cursor = base64.urlsafe_b64encode(
                json.dumps([last.started_at.isoformat(), str(last.id)]).encode()
            ).decode()
        return RunPage(items=items[:limit], next_cursor=next_cursor)

    def save_static(self, owner, project, identity, payload):
        checked = RepositoryAnalysisResponse.model_validate_json(payload.model_dump_json())
        raw = checked.model_dump_json()
        with database_transaction(self.engine) as connection:
            tx = BoundProjectStore(connection)
            row = self.row(tx, owner, project, identity)
            self.view(row)
            if (
                checked.report.identity.base.commit != row["base"]
                or checked.report.identity.target.commit != row["target"]
                or checked.repository.repository_url != row["repository_url"]
            ):
                raise AuthFailure("report_identity_mismatch", 409)
            tx.execute(
                "UPDATE smartregression.web_runs SET payload=CAST(:payload AS json"
                "b),payload_digest=:digest,"
                "repository_id=:repo,analysis_run_id=:analysis,report_id=:report "
                "WHERE owner_id=:owner AND project_id=:project AND id=:id AND stat"
                "us='running' AND payload IS NULL",
                owner=owner,
                project=project,
                id=identity,
                payload=raw,
                digest=hashlib.sha256(raw.encode()).hexdigest(),
                repo=checked.report.identity.repository_id,
                analysis=checked.report.identity.run_id,
                report=checked.report.report_id,
            )

    @staticmethod
    def _finish(tx, owner, project, identity, error):
        changed = tx.execute(
            "UPDATE smartregression.web_runs SET status=:status,error_code=:er"
            "ror,finished_at=CURRENT_TIMESTAMP "
            "WHERE owner_id=:owner AND project_id=:project AND id=:id AND stat"
            "us IN ('queued','running') RETURNING id",
            owner=owner,
            project=project,
            id=identity,
            status="failed" if error else "completed",
            error=error,
        ).first()
        if changed:
            tx.activity(owner, project, "run_failed" if error else "run_completed", identity)

    def finish(self, owner, project, identity, error):
        with database_transaction(self.engine) as connection:
            self._finish(BoundProjectStore(connection), owner, project, identity, error)

    def report(self, owner, project, identity):
        with database_transaction(self.engine) as connection:
            tx = BoundProjectStore(connection)
            tx.get(owner, project)
            row = self.row(tx, owner, project, identity)
            view = self.view(row)
            if row["payload"] is None:
                raise AuthFailure("report_not_ready", 409)
            payload = RepositoryAnalysisResponse.model_validate(row["payload"])
            if (
                hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
                != row["payload_digest"]
            ):
                raise AuthFailure("report_integrity_failed", 503)
            latest = tx.execute(
                "SELECT result FROM smartregression.web_ai_requests "
                "WHERE owner_id=:owner AND run_id=:run AND action='commit' "
                "AND status='completed' ORDER BY created_at DESC,id DESC LIMIT 1",
                owner=owner,
                run=identity,
            ).scalar()
            if latest:
                payload = RepositoryAnalysisResponse.model_validate(
                    payload.model_dump() | {"narrative": latest}
                )
            return SavedRunReport(run=view, payload=payload)

    def interrupt(self):
        # Composition holds an exclusive process lease before recovering prior work.
        with database_transaction(self.engine) as connection:
            tx = BoundProjectStore(connection)
            rows = tx.execute(
                "UPDATE smartregression.web_runs SET status='interrupted',error_co"
                "de='service_restarted',"
                "finished_at=CURRENT_TIMESTAMP WHERE status IN ('queued','running'"
                ") RETURNING owner_id,project_id,id"
            ).all()
            for owner, project, identity in rows:
                tx.activity(str(owner), str(project), "run_interrupted", str(identity))

    def export_activity(self, owner, project, identity):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            tx.activity(owner, project, "export_generated", identity)

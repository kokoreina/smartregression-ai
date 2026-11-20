"""Atomic cross-account campaign budgets and immutable AI attempt records."""

import json
from uuid import uuid4

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.project_store import BoundProjectStore
from smartregression.adapters.storage.web_run_store import PostgresWebRunStore
from smartregression.application.auth import AuthFailure
from smartregression.contracts.ai_requests import AiJob, AiQuota
from smartregression.contracts.repository import NarrativeResult


def view(row):
    if row is None:
        raise AuthFailure("ai_request_not_found", 404)
    return AiJob.model_validate(
        {key: row[key] for key in AiJob.model_fields if key != "schema_version"}
    )


class PostgresAiStore:
    def __init__(self, engine):
        self.engine = engine

    def reserve(self, owner, project, run, body, digest, *, scope=None):
        action = body.action if scope is not None else "commit"
        scope_key = scope["key"] if scope is not None else "run:" + run
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.execute("SELECT pg_advisory_xact_lock(741031)")
            tx.lock_owner(owner)
            current = tx.get(owner, project, lock=True)
            if run is not None:
                saved = PostgresWebRunStore.row(tx, owner, project, run)
                if saved is None or saved["payload"] is None:
                    raise AuthFailure("report_not_ready", 409)
            old = (
                tx.execute(
                    "SELECT * FROM smartregression.web_ai_requests WHERE owner_id"
                    "=:owner AND project_id=:project AND scope_key=:scope "
                    "AND action=:action AND idempotency_"
                    "key=:key",
                    owner=owner,
                    project=project,
                    scope=scope_key,
                    action=action,
                    key=body.idempotency_key,
                )
                .mappings()
                .first()
            )
            if old:
                if old["input_digest"] != digest:
                    raise AuthFailure("idempotency_conflict", 409)
                return view(old), False, old["batch"], old["campaign_id"]
            if current.archived:
                raise AuthFailure("project_archived", 409)
            active = (
                tx.execute(
                    "SELECT owner_id FROM smartregression.web_ai_requests "
                    "WHERE status IN ('queued','running') UNION ALL "
                    "SELECT owner_id FROM smartregression.web_runs "
                    "WHERE status IN ('queued','running')"
                )
                .scalars()
                .all()
            )
            if owner in {str(value) for value in active} or len(active) >= 2:
                raise AuthFailure("ai_busy", 409)
            grants = (
                tx.execute(
                    "SELECT g.*,c.max_calls AS global_calls,c.cap_micro_usd AS gl"
                    "obal_cap FROM smartregression.web_ai_grants g JOIN smartregr"
                    "ession.web_ai_campaigns c ON c.id=g.campaign_id WHERE g.owne"
                    "r_id=:owner "
                    + (
                        "AND g.campaign_id=:restricted_campaign "
                        if scope and scope.get("campaign")
                        else ""
                    )
                    + "ORDER BY g.campaign_id",
                    owner=owner,
                    **(
                        {"restricted_campaign": scope["campaign"]}
                        if scope and scope.get("campaign")
                        else {}
                    ),
                )
                .mappings()
                .all()
            )
            for grant in grants:
                total = (
                    tx.execute(
                        "SELECT count(*) AS calls,coalesce(sum(coalesce(actual_micro_"
                        "usd,reservation_micro_usd)),0) AS amount FROM smartregressio"
                        "n.web_ai_requests WHERE campaign_id=:campaign",
                        campaign=grant["campaign_id"],
                    )
                    .mappings()
                    .one()
                )
                personal = (
                    tx.execute(
                        "SELECT count(*) AS calls,coalesce(sum(coalesce(actual_micro_"
                        "usd,reservation_micro_usd)),0) AS amount FROM smartregressio"
                        "n.web_ai_requests WHERE campaign_id=:campaign AND owner_id=:"
                        "owner",
                        campaign=grant["campaign_id"],
                        owner=owner,
                    )
                    .mappings()
                    .one()
                )
                if (
                    total["calls"] < grant["global_calls"]
                    and personal["calls"] < grant["max_calls"]
                    and total["amount"] + 20000 <= grant["global_cap"]
                    and personal["amount"] + 20000 <= grant["cap_micro_usd"]
                ):
                    break
            else:
                raise AuthFailure("ai_quota_exhausted", 403)
            identity = str(uuid4())
            number = total["calls"] + 1
            batch = (number - 1) // 5 + 1
            row = (
                tx.execute(
                    "INSERT INTO smartregression.web_ai_requests(id,owner_id,proj"
                    "ect_id,run_id,campaign_id,idempotency_key,input_digest,actio"
                    "n,status,reservation_micro_usd,campaign_call,batch,scope_key,context_hash,"
                    "provenance,snapshot_commit,snapshot_config) VALUES(:"
                    "id,:owner,:project,:run,:campaign,:key,:digest,:action,'que"
                    "ued',20000,:number,:batch,:scope,:hash,CAST(:provenance AS jsonb),"
                    ":commit,:config) RETURNING *",
                    id=identity,
                    owner=owner,
                    project=project,
                    run=run,
                    campaign=grant["campaign_id"],
                    key=body.idempotency_key,
                    digest=digest,
                    number=number,
                    batch=batch,
                    action=action,
                    scope=scope_key,
                    hash=scope["hash"] if scope else None,
                    provenance=json.dumps(scope["provenance"] if scope else {}),
                    commit=scope["commit"] if scope else None,
                    config=scope["config"] if scope else None,
                )
                .mappings()
                .one()
            )
            tx.execute(
                "UPDATE smartregression.web_runs SET ai_status='running' WHER"
                "E owner_id=:owner AND id=:run",
                owner=owner,
                run=run,
            )
            tx.activity(owner, project, "ai_requested", identity)
            return view(row), True, batch, grant["campaign_id"]

    def get(self, owner, project, run, identity):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            return view(
                tx.execute(
                    "SELECT * FROM smartregression.web_ai_requests WHERE owner_id"
                    "=:owner AND project_id=:project AND run_id=:run AND id=:id",
                    owner=owner,
                    project=project,
                    run=run,
                    id=identity,
                )
                .mappings()
                .first()
            )

    def scoped_get(self, owner, project, identity):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            return view(
                tx.execute(
                    "SELECT * FROM smartregression.web_ai_requests WHERE owner_id=:owner "
                    "AND project_id=:project AND id=:id AND run_id IS NULL",
                    owner=owner,
                    project=project,
                    id=identity,
                )
                .mappings()
                .first()
            )

    def run_list(self, owner, project, identity):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            return [
                view(row)
                for row in tx.execute(
                    "SELECT * FROM smartregression.web_ai_requests WHERE owner_id=:owner "
                    "AND project_id=:project AND run_id=:run ORDER BY created_at,id LIMIT 100",
                    owner=owner,
                    project=project,
                    run=identity,
                ).mappings()
            ]

    def scoped_list(self, owner, project, commit):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            return [
                view(row)
                for row in tx.execute(
                    "SELECT * FROM smartregression.web_ai_requests WHERE owner_id=:owner "
                    "AND project_id=:project AND snapshot_commit=:commit "
                    "ORDER BY created_at DESC,id DESC LIMIT 100",
                    owner=owner,
                    project=project,
                    commit=commit,
                ).mappings()
            ]

    def start(self, owner, identity):
        with database_transaction(self.engine) as conn:
            return (
                BoundProjectStore(conn)
                .execute(
                    "UPDATE smartregression.web_ai_requests SET status='running' "
                    "WHERE owner_id=:owner AND id=:id AND status='queued' RETURNI"
                    "NG id",
                    owner=owner,
                    id=identity,
                )
                .first()
                is not None
            )

    def finish(self, owner, identity, result):
        checked = NarrativeResult.model_validate_json(result.model_dump_json())
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            row = tx.execute(
                "UPDATE smartregression.web_ai_requests SET status=:status,re"
                "sult=CAST(:result AS jsonb),finished_at=CURRENT_TIMESTAMP WH"
                "ERE owner_id=:owner AND id=:id AND status IN ('queued','runn"
                "ing') RETURNING project_id,run_id",
                owner=owner,
                id=identity,
                status=checked.status,
                result=checked.model_dump_json(),
            ).first()
            if row:
                tx.execute(
                    "UPDATE smartregression.web_runs SET ai_status=:status WHERE "
                    "owner_id=:owner AND id=:run",
                    owner=owner,
                    run=row.run_id,
                    status=checked.status,
                )
                tx.activity(owner, str(row.project_id), "ai_" + checked.status, identity)

    def quota(self, owner):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            grant = (
                tx.execute(
                    "SELECT coalesce(sum(max_calls),0) AS calls,coalesce(sum(cap_"
                    "micro_usd),0) AS cap FROM smartregression.web_ai_grants WHER"
                    "E owner_id=:owner",
                    owner=owner,
                )
                .mappings()
                .one()
            )
            usage = (
                tx.execute(
                    "SELECT count(*) AS calls,coalesce(sum(reservation_micro_usd)"
                    ",0) AS reserved,coalesce(sum(actual_micro_usd),0) AS known,c"
                    "ount(*) FILTER(WHERE actual_micro_usd IS NULL) AS unknown FR"
                    "OM smartregression.web_ai_requests WHERE owner_id=:owner",
                    owner=owner,
                )
                .mappings()
                .one()
            )
            return AiQuota(
                granted_calls=grant["calls"],
                used_calls=usage["calls"],
                cap_micro_usd=grant["cap"],
                reserved_micro_usd=usage["reserved"],
                known_actual_micro_usd=usage["known"],
                unknown_actual_count=usage["unknown"],
            )

    def interrupt(self):
        # A lost process may already have reached the provider: retain reservations.
        failure = NarrativeResult(status="failed", error_code="provider_timeout").model_dump_json()
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            rows = tx.execute(
                "UPDATE smartregression.web_ai_requests SET status='failed',r"
                "esult=CAST(:result AS jsonb),"
                "finished_at=CURRENT_TIMESTAMP WHERE status IN ('queued','running') "
                "RETURNING owner_id,project_id,run_id,id",
                result=failure,
            ).all()
            for owner, project, run, identity in rows:
                tx.execute(
                    "UPDATE smartregression.web_runs SET ai_status='failed' WHERE"
                    " owner_id=:owner AND id=:run",
                    owner=owner,
                    run=run,
                )
                tx.activity(str(owner), str(project), "ai_interrupted", str(identity))

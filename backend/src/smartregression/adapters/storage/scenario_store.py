"""Immutable scenario payloads; retry keys bind the complete request digest."""

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.explorer_store import digest, encoded
from smartregression.adapters.storage.project_store import BoundProjectStore
from smartregression.application.auth import AuthFailure
from smartregression.application.projects import decode_cursor, page_cursor
from smartregression.contracts.scenarios import Scenario


def scenario(row):
    if row is None:
        raise AuthFailure("scenario_not_found", 404)
    if digest(row["payload"]) != row["payload_digest"]:
        raise AuthFailure("scenario_integrity_failed", 503)
    value = Scenario.model_validate(row["payload"])
    if (
        str(value.project_id) != str(row["project_id"])
        or value.mode != row["mode"]
        or str(value.id) != str(row["id"])
        or value.baseline != row["baseline"]
        or value.config_digest != row["config_digest"]
        or value.input_digest != row["input_digest"]
    ):
        raise AuthFailure("scenario_identity_mismatch", 503)
    return value


class PostgresScenarioStore:
    def __init__(self, engine):
        self.engine = engine

    def save(self, owner, project, key, value):
        payload = value.model_dump(mode="json")
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.execute("SELECT pg_advisory_xact_lock(741031)")
            tx.lock_owner(owner)
            current = tx.get(owner, project, lock=True)
            if current.archived:
                raise AuthFailure("project_archived", 409)
            old = (
                tx.execute(
                    "SELECT * FROM smartregression.web_scenarios WHERE "
                    "owner_id=:owner AND project_id=:project AND "
                    "idempotency_key=:key",
                    owner=owner,
                    project=project,
                    key=key,
                )
                .mappings()
                .first()
            )
            if old:
                if old["input_digest"] != value.input_digest:
                    raise AuthFailure("idempotency_conflict", 409)
                return scenario(old)
            tx.execute(
                "INSERT INTO smartregression.web_scenarios(id,owner_id,"
                "project_id,baseline,config_digest,idempotency_key,"
                "input_digest,mode,payload,payload_digest,created_at) "
                "VALUES(:id,:owner,:project,:base,:config,:key,:input,:mode,"
                "CAST(:payload AS jsonb),:digest,:created)",
                id=str(value.id),
                owner=owner,
                project=project,
                base=value.baseline,
                config=value.config_digest,
                key=key,
                input=value.input_digest,
                mode=value.mode,
                payload=encoded(payload),
                digest=digest(payload),
                created=value.created_at,
            )
            tx.activity(owner, project, "scenario_created", str(value.id))
            return value

    def get(self, owner, project, identity):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            row = (
                tx.execute(
                    "SELECT * FROM smartregression.web_scenarios WHERE "
                    "owner_id=:owner AND project_id=:project AND id=:id",
                    owner=owner,
                    project=project,
                    id=identity,
                )
                .mappings()
                .first()
            )
            return scenario(row)

    def list(self, owner, project, cursor=None, limit=25):
        params = dict(owner=owner, project=project, limit=limit + 1)
        clause = ""
        decoded = decode_cursor(cursor)
        if decoded:
            clause = " AND (created_at,id)<(:stamp,CAST(:cursor_id AS uuid))"
            params.update(stamp=decoded[0], cursor_id=decoded[1])
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            rows = (
                tx.execute(
                    "SELECT * FROM smartregression.web_scenarios WHERE "
                    "owner_id=:owner AND project_id=:project"
                    + clause
                    + " ORDER BY created_at DESC,id DESC LIMIT :limit",
                    **params,
                )
                .mappings()
                .all()
            )
            items = [scenario(row) for row in rows]
            return items[:limit], page_cursor(items, limit)

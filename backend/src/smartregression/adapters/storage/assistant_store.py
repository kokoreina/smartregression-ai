"""PostgreSQL owner isolation and atomic progress/notification publication."""

from datetime import UTC, datetime
from uuid import uuid4

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.explorer_store import digest, encoded
from smartregression.adapters.storage.project_store import BoundProjectStore
from smartregression.application.auth import AuthFailure
from smartregression.contracts.repo_assistant import (
    AssistantMessage,
    AssistantReply,
    AssistantThread,
    ChangeNotification,
    ChangeReport,
    RepositoryWatch,
)


def thread_view(row):
    if row is None:
        raise AuthFailure("thread_not_found", 404)
    return AssistantThread.model_validate(
        {k: row[k] for k in AssistantThread.model_fields if k != "schema_version"}
    )


def watch_view(row):
    if row is None:
        return None
    values = {k: row[k] for k in RepositoryWatch.model_fields if k != "schema_version"}
    values["pending"] = row["pending"] or (
        row["lease_until"] is not None and row["lease_until"] > datetime.now(UTC)
    )
    return RepositoryWatch.model_validate(values)


class PostgresAssistantStore:
    def __init__(self, engine):
        self.engine = engine

    def transaction(self):
        return database_transaction(self.engine)

    @staticmethod
    def bound(conn, owner, project, *, write=False):
        tx = BoundProjectStore(conn)
        if write:
            tx.lock_owner(owner)
        current = tx.get(owner, project, lock=write)
        if write and current.archived:
            raise AuthFailure("project_archived", 409)
        return tx

    def threads(self, owner, project):
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project)
            return [
                thread_view(r)
                for r in tx.execute(
                    "SELECT * FROM smartregression.web_assistant_threads WHERE owner_id=:owner "
                    "AND project_id=:project ORDER BY created_at DESC,id DESC LIMIT 30",
                    owner=owner,
                    project=project,
                ).mappings()
            ]

    def thread(self, owner, project, identity):
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project)
            return thread_view(
                tx.execute(
                    "SELECT * FROM smartregression.web_assistant_threads "
                    "WHERE owner_id=:owner AND project_id=:project AND id=:id",
                    owner=owner,
                    project=project,
                    id=identity,
                )
                .mappings()
                .first()
            )

    def create_thread(self, owner, project, body, config):
        params = dict(owner=owner, project=project, key=body.idempotency_key)
        signature = digest(body.model_dump())
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project, write=True)
            old = (
                tx.execute(
                    "SELECT * FROM smartregression.web_assistant_threads WHERE "
                    "owner_id=:owner AND project_id=:project AND idempotency_key=:key",
                    **params,
                )
                .mappings()
                .first()
            )
            if old:
                if old["input_digest"] != signature:
                    raise AuthFailure("idempotency_conflict", 409)
                return thread_view(old)
            if (
                tx.execute(
                    "SELECT count(*) FROM smartregression.web_assistant_threads WHERE "
                    "owner_id=:owner AND project_id=:project",
                    owner=owner,
                    project=project,
                ).scalar_one()
                >= 100
            ):
                raise AuthFailure("thread_limit", 409)
            return thread_view(
                tx.execute(
                    "INSERT INTO smartregression.web_assistant_threads "
                    "(id,owner_id,project_id,commit,config_digest,title,idempotency_key,input_digest)"
                    " "
                    "VALUES(:id,:owner,:project,:commit,:config,:title,:key,:signature) "
                    "RETURNING *",
                    **params,
                    id=str(uuid4()),
                    commit=body.commit,
                    config=config,
                    title=body.title,
                    signature=signature,
                )
                .mappings()
                .one()
            )

    def messages(self, owner, project, identity):
        self.thread(owner, project, identity)
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project)
            rows = (
                tx.execute(
                    "SELECT * FROM smartregression.web_assistant_messages WHERE "
                    "owner_id=:owner AND project_id=:project AND thread_id=:id "
                    "ORDER BY created_at,id LIMIT 100",
                    owner=owner,
                    project=project,
                    id=identity,
                )
                .mappings()
                .all()
            )
            return [self.message_view(r) for r in rows]

    @staticmethod
    def message_view(row):
        if digest(row["reply"]) != row["reply_digest"]:
            raise AuthFailure("message_integrity_failed", 503)
        return AssistantMessage(
            id=row["id"],
            thread_id=row["thread_id"],
            question=row["question"],
            reply=AssistantReply.model_validate(row["reply"]),
            created_at=row["created_at"],
        ), row["ai_id"]

    def find_message(self, owner, project, identity, key, signature):
        self.thread(owner, project, identity)
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project)
            row = (
                tx.execute(
                    "SELECT * FROM smartregression.web_assistant_messages WHERE "
                    "owner_id=:owner AND project_id=:project AND thread_id=:id AND "
                    "idempotency_key=:key",
                    owner=owner,
                    project=project,
                    id=identity,
                    key=key,
                )
                .mappings()
                .first()
            )
            if row:
                if row["input_digest"] != signature:
                    raise AuthFailure("idempotency_conflict", 409)
                return self.message_view(row)
            return None

    def save_message(self, owner, project, thread, body, signature, reply, ai_id=None):
        # Snippets are recreated from the pinned snapshot, not copied into chat history.
        payload = reply.model_copy(update={"excerpts": []}).model_dump(mode="json")
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project, write=True)
            if (
                tx.execute(
                    "SELECT count(*) FROM smartregression.web_assistant_messages WHERE "
                    "thread_id=:thread",
                    thread=thread,
                ).scalar_one()
                >= 100
            ):
                raise AuthFailure("message_limit", 409)
            tx.execute(
                "INSERT INTO smartregression.web_assistant_messages "
                "(id,owner_id,project_id,thread_id,idempotency_key,input_digest,question,reply,reply_digest,ai_id)"
                " "
                "VALUES(:id,:owner,:project,:thread,:key,:signature,:question,CAST(:reply AS "
                "jsonb),:rd,:ai) "
                "ON CONFLICT(owner_id,project_id,thread_id,idempotency_key) DO NOTHING",
                id=str(uuid4()),
                owner=owner,
                project=project,
                thread=thread,
                key=body.idempotency_key,
                signature=signature,
                question=body.question,
                reply=encoded(payload),
                rd=digest(payload),
                ai=ai_id,
            )
        return self.find_message(owner, project, thread, body.idempotency_key, signature)

    def advance_ai(
        self, owner: str, project: str, thread: str, previous: str, current: str
    ) -> bool:
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project, write=True)
            return bool(
                tx.execute(
                    "UPDATE smartregression.web_assistant_messages SET ai_id=:current "
                    "WHERE owner_id=:owner AND project_id=:project AND thread_id=:thread "
                    "AND ai_id=:previous "
                    "RETURNING id",
                    owner=owner,
                    project=project,
                    thread=thread,
                    previous=previous,
                    current=current,
                ).first()
            )

    def delete_thread(self, owner, project, identity):
        self.thread(owner, project, identity)
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project, write=True)
            tx.execute(
                "DELETE FROM smartregression.web_assistant_messages WHERE owner_id=:owner "
                "AND project_id=:project AND thread_id=:id",
                owner=owner,
                project=project,
                id=identity,
            )
            tx.execute(
                "DELETE FROM smartregression.web_assistant_threads WHERE owner_id=:owner "
                "AND project_id=:project AND id=:id",
                owner=owner,
                project=project,
                id=identity,
            )

    def watch(self, owner, project):
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project)
            return watch_view(
                tx.execute(
                    "SELECT * FROM smartregression.web_repo_watches WHERE "
                    "owner_id=:owner AND project_id=:project",
                    owner=owner,
                    project=project,
                )
                .mappings()
                .first()
            )

    def save_watch(self, owner, project, body, commit):
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project, write=True)
            old = (
                tx.execute(
                    "SELECT * FROM smartregression.web_repo_watches WHERE owner_id=:owner "
                    "AND project_id=:project FOR UPDATE",
                    owner=owner,
                    project=project,
                )
                .mappings()
                .first()
            )
            if (old["version"] if old else 0) != body.version:
                raise AuthFailure("version_conflict", 409)
            baseline = old["last_commit"] if old and old["branch"] == body.branch else commit
            row = (
                tx.execute(
                    "INSERT INTO smartregression.web_repo_watches "
                    "(owner_id,project_id,branch,paths,automatic,interval_seconds,version,last_commit,checked_at,next_check_at)"
                    " "
                    "VALUES(:owner,:project,:branch,CAST(:paths AS "
                    "jsonb),:auto,:interval,:version,:commit,now(), "
                    "now()+make_interval(secs=>:interval)) ON CONFLICT(owner_id,project_id) "
                    "DO UPDATE SET "
                    "branch=EXCLUDED.branch,paths=EXCLUDED.paths,automatic=EXCLUDED.automatic,interval_seconds=EXCLUDED.interval_seconds,"
                    "version=EXCLUDED.version,last_commit=EXCLUDED.last_commit,next_check_at=EXCLUDED.next_check_at,"
                    "pending=FALSE,lease_token=NULL,lease_until=NULL,error_code=NULL RETURNING *",
                    owner=owner,
                    project=project,
                    branch=body.branch,
                    paths=encoded(body.paths),
                    auto=body.automatic,
                    interval=body.interval_seconds,
                    version=body.version + 1,
                    commit=baseline,
                )
                .mappings()
                .one()
            )
            return watch_view(row)

    def schedule(self, owner, project):
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project, write=True)
            row = (
                tx.execute(
                    "UPDATE smartregression.web_repo_watches SET pending=TRUE,next_check_at=now() "
                    "WHERE owner_id=:owner AND project_id=:project RETURNING *",
                    owner=owner,
                    project=project,
                )
                .mappings()
                .first()
            )
            if row is None:
                raise AuthFailure("watch_not_configured", 409)
            return watch_view(row)

    def claim(self, owner=None, project=None):
        with self.transaction() as conn:
            tx = BoundProjectStore(conn)
            row = (
                tx.execute(
                    "SELECT w.*,p.repository_url FROM smartregression.web_repo_watches w "
                    "JOIN smartregression.web_projects p ON p.id=w.project_id AND "
                    "p.owner_id=w.owner_id "
                    "JOIN smartregression.web_users u ON u.id=w.owner_id "
                    "WHERE NOT p.archived AND u.enabled AND u.verified AND (w.pending OR "
                    "(w.automatic AND w.next_check_at<=now()) OR w.lease_token IS NOT NULL) "
                    "AND (w.lease_until IS NULL OR w.lease_until<now()) "
                    + (
                        "AND w.owner_id=:owner AND w.project_id=:project "
                        if owner is not None
                        else ""
                    )
                    + "ORDER BY w.next_check_at FOR UPDATE OF w SKIP LOCKED LIMIT 1",
                    **({"owner": owner, "project": project} if owner is not None else {}),
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            job = dict(row)
            job["lease_token"] = str(uuid4())
            tx.execute(
                "UPDATE smartregression.web_repo_watches SET pending=FALSE,lease_token=:token,"
                "lease_until=now()+interval '10 minutes' WHERE owner_id=:owner AND "
                "project_id=:project",
                token=job["lease_token"],
                owner=job["owner_id"],
                project=job["project_id"],
            )
            return job

    def finish(self, job, target=None, report=None, error=None):
        with self.transaction() as conn:
            tx = BoundProjectStore(conn)
            current = (
                tx.execute(
                    "SELECT w.* FROM smartregression.web_repo_watches w "
                    "JOIN smartregression.web_projects p ON p.id=w.project_id AND "
                    "p.owner_id=w.owner_id "
                    "JOIN smartregression.web_users u ON u.id=w.owner_id "
                    "WHERE w.owner_id=:owner AND w.project_id=:project AND w.version=:version "
                    "AND w.lease_token=:token AND NOT p.archived AND u.verified AND u.enabled "
                    "FOR UPDATE OF w",
                    owner=job["owner_id"],
                    project=job["project_id"],
                    version=job["version"],
                    token=job["lease_token"],
                )
                .mappings()
                .first()
            )
            if current is None:
                return False
            if report is not None:
                payload = report.model_dump(mode="json")
                identity = digest(
                    {
                        "branch": report.branch,
                        "base": report.base,
                        "target": report.target,
                        "config": report.config_digest,
                        "scope": report.scope,
                    }
                )
                tx.execute(
                    "INSERT INTO smartregression.web_change_notifications "
                    "(id,owner_id,project_id,report,report_digest,identity_digest) "
                    "VALUES(:id,:owner,:project,CAST(:report AS jsonb),:rd,:identity) "
                    "ON CONFLICT(owner_id,project_id,identity_digest) DO NOTHING",
                    id=str(uuid4()),
                    owner=job["owner_id"],
                    project=job["project_id"],
                    report=encoded(payload),
                    rd=digest(payload),
                    identity=identity,
                )
            tx.execute(
                "UPDATE smartregression.web_repo_watches SET "
                "last_commit=coalesce(:commit,last_commit),"
                "checked_at=now(),error_code=:error,lease_token=NULL,lease_until=NULL,"
                "next_check_at=CASE WHEN :error='github_rate_limit' "
                "THEN now()+make_interval(secs=>greatest(interval_seconds,3600)) "
                "WHEN pending THEN now() ELSE now()+make_interval(secs=>interval_seconds) END, "
                "pending=CASE WHEN :error='github_rate_limit' THEN FALSE ELSE pending END "
                "WHERE owner_id=:owner AND project_id=:project",
                commit=target,
                error=error,
                owner=job["owner_id"],
                project=job["project_id"],
            )
            return True

    def notifications(self, owner, project):
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project)
            values = []
            for row in tx.execute(
                "SELECT * FROM smartregression.web_change_notifications WHERE "
                "owner_id=:owner AND project_id=:project ORDER BY created_at DESC,id DESC LIMIT 30",
                owner=owner,
                project=project,
            ).mappings():
                if digest(row["report"]) != row["report_digest"]:
                    raise AuthFailure("notification_integrity_failed", 503)
                values.append(
                    ChangeNotification(
                        id=row["id"],
                        created_at=row["created_at"],
                        read_at=row["read_at"],
                        report=ChangeReport.model_validate(row["report"]),
                    )
                )
            return values

    def read_notification(self, owner, project, identity):
        with self.transaction() as conn:
            tx = self.bound(conn, owner, project)
            if not tx.execute(
                "UPDATE smartregression.web_change_notifications SET "
                "read_at=coalesce(read_at,now()) "
                "WHERE owner_id=:owner AND project_id=:project AND id=:id RETURNING id",
                owner=owner,
                project=project,
                id=identity,
            ).first():
                raise AuthFailure("notification_not_found", 404)

    def delivery(self, identity, signature, repository, event, branch, actor):
        with self.transaction() as conn:
            tx = BoundProjectStore(conn)
            row = tx.execute(
                "INSERT INTO smartregression.web_github_deliveries "
                "(id,payload_digest,repository,event,branch,actor) "
                "VALUES(:id,:digest,:repo,:event,:branch,:actor) "
                "ON CONFLICT(id) DO NOTHING RETURNING id",
                id=identity,
                digest=signature,
                repo=repository,
                event=event,
                branch=branch,
                actor=actor,
            ).first()
            if row is None:
                old = tx.execute(
                    "SELECT payload_digest FROM smartregression.web_github_deliveries WHERE id=:id",
                    id=identity,
                ).scalar_one()
                if old != signature:
                    raise AuthFailure("webhook_delivery_conflict", 409)
                return True, 0
            result = tx.execute(
                "UPDATE smartregression.web_repo_watches w SET pending=TRUE,next_check_at=now() "
                "FROM smartregression.web_projects p WHERE p.owner_id=w.owner_id AND "
                "p.id=w.project_id "
                "AND NOT p.archived AND lower(p.repository_url)=:url AND w.branch=:branch "
                "AND w.automatic AND (w.error_code IS DISTINCT FROM 'github_rate_limit' "
                "OR w.next_check_at<=now())",
                url="https://github.com/" + repository.lower(),
                branch=branch,
            )
            return False, result.rowcount

"""Owner-scoped optimistic notes and mutable view state; archive never cascades."""

import json
from uuid import uuid4

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.project_store import BoundProjectStore
from smartregression.application.auth import AuthFailure
from smartregression.application.projects import decode_cursor, page_cursor
from smartregression.contracts.notes import Note, NotePage, ViewState
from smartregression.core.explorer.graph import PARSER_CONFIG


def note(row):
    if row is None:
        raise AuthFailure("note_not_found", 404)
    return Note.model_validate(
        {k: v for k, v in row.items() if k not in {"owner_id", "project_id"}}
    )


def stale(tx, owner, project, commit, path):
    if path is None:
        return False
    cached = tx.execute(
        "SELECT payload FROM smartregression.web_explorer_snapshots "
        "WHERE owner_id=:owner AND project_id=:project AND "
        "commit=:commit AND config_digest=:config",
        owner=owner,
        project=project,
        commit=commit,
        config=PARSER_CONFIG,
    ).scalar()
    if cached is None:
        return None
    return not any(entry["path"] == path for entry in cached["tree"]["entries"])


class PostgresNoteStore:
    def __init__(self, engine):
        self.engine = engine

    def create(self, owner, project, body):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.execute("SELECT pg_advisory_xact_lock(741031)")
            tx.lock_owner(owner)
            tx.get(owner, project, lock=True)
            if stale(tx, owner, project, body.commit, body.path) is not False:
                raise AuthFailure("note_anchor_not_ready", 409)
            identity = str(uuid4())
            row = (
                tx.execute(
                    "INSERT INTO smartregression.web_notes(id,owner_id,"
                    "project_id,kind,commit,path,title,body) VALUES(:id,:owner,"
                    ":project,:kind,:commit,:path,:title,:body) RETURNING *",
                    id=identity,
                    owner=owner,
                    project=project,
                    **body.model_dump(),
                )
                .mappings()
                .one()
            )
            tx.activity(
                owner, project, "note_created" if body.kind == "note" else "pin_created", identity
            )
            return note(row)

    def update(self, owner, project, identity, body):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.lock_owner(owner)
            tx.get(owner, project, lock=True)
            current = (
                tx.execute(
                    "SELECT * FROM smartregression.web_notes WHERE "
                    "owner_id=:owner AND project_id=:project AND id=:id FOR "
                    "UPDATE",
                    owner=owner,
                    project=project,
                    id=identity,
                )
                .mappings()
                .first()
            )
            previous = note(current)
            if previous.version != body.version:
                raise AuthFailure("version_conflict", 409)
            row = (
                tx.execute(
                    "UPDATE smartregression.web_notes SET title=:title,"
                    "body=:body,archived=:archived,version=version+1,"
                    "updated_at=CURRENT_TIMESTAMP WHERE owner_id=:owner AND "
                    "project_id=:project AND id=:id RETURNING *",
                    owner=owner,
                    project=project,
                    id=identity,
                    title=body.title,
                    body=body.body,
                    archived=body.archived,
                )
                .mappings()
                .one()
            )
            tx.activity(
                owner, project, "note_archived" if body.archived else "note_updated", identity
            )
            return note(row)

    def list(self, owner, project, cursor=None, limit=25, current=None):
        decoded = decode_cursor(cursor)
        params = dict(owner=owner, project=project, limit=limit + 1)
        clause = ""
        if decoded:
            clause = " AND (created_at,id)<(:stamp,CAST(:cursor_id AS uuid))"
            params.update(stamp=decoded[0], cursor_id=decoded[1])
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            rows = (
                tx.execute(
                    "SELECT * FROM smartregression.web_notes WHERE "
                    "owner_id=:owner AND project_id=:project AND NOT archived"
                    + clause
                    + " ORDER BY created_at DESC,id DESC LIMIT :limit",
                    **params,
                )
                .mappings()
                .all()
            )
            items = [note(row) for row in rows]
            for item in items:
                item.stale = stale(tx, owner, project, current or item.commit, item.path)
            return NotePage(items=items[:limit], next_cursor=page_cursor(items, limit))

    def view(self, owner, project):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            row = (
                tx.execute(
                    "SELECT * FROM smartregression.web_view_states WHERE "
                    "owner_id=:owner AND project_id=:project",
                    owner=owner,
                    project=project,
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            value = ViewState.model_validate(
                {k: v for k, v in row.items() if k not in {"owner_id", "project_id"}}
            )
            value.stale = stale(tx, owner, project, value.commit, value.path)
            return value

    def save_view(self, owner, project, body):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.execute("SELECT pg_advisory_xact_lock(741031)")
            tx.lock_owner(owner)
            tx.get(owner, project, lock=True)
            row = tx.execute(
                "SELECT version FROM smartregression.web_view_states WHERE "
                "owner_id=:owner AND project_id=:project FOR UPDATE",
                owner=owner,
                project=project,
            ).first()
            version = row.version if row else 0
            if version != body.version:
                raise AuthFailure("version_conflict", 409)
            values = body.model_dump() | dict(
                owner=owner,
                project=project,
                version=version + 1,
                expanded_paths=json.dumps(body.expanded_paths),
            )
            saved = (
                tx.execute(
                    "INSERT INTO smartregression.web_view_states(owner_id,"
                    "project_id,version,commit,path,tab,expanded_paths,"
                    "focus_only) VALUES(:owner,:project,:version,:commit,:path,"
                    ":tab,CAST(:expanded_paths AS jsonb),:focus_only) ON "
                    "CONFLICT(owner_id,project_id) DO UPDATE SET "
                    "version=EXCLUDED.version,commit=EXCLUDED.commit,"
                    "path=EXCLUDED.path,tab=EXCLUDED.tab,"
                    "expanded_paths=EXCLUDED.expanded_paths,"
                    "focus_only=EXCLUDED.focus_only,updated_at=CURRENT_TIMESTAMP "
                    "RETURNING *",
                    **values,
                )
                .mappings()
                .one()
            )
            return ViewState.model_validate(
                {k: v for k, v in saved.items() if k not in {"owner_id", "project_id"}}
            )

"""Bound PostgreSQL personal-project persistence, including atomic activity writes."""

import hashlib
from contextlib import contextmanager
from uuid import uuid4

from sqlalchemy import text

from smartregression.adapters.storage.connection import database_transaction
from smartregression.application.auth import AuthFailure
from smartregression.contracts.projects import Activity, Project


class PostgresProjectStore:
    def __init__(self, engine):
        self.engine = engine

    @contextmanager
    def transaction(self):
        with database_transaction(self.engine) as connection:
            yield BoundProjectStore(connection)


class BoundProjectStore:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, statement, **parameters):
        return self.connection.execute(text(statement), parameters)

    def lock_owner(self, owner):
        row = self.execute(
            "SELECT verified,enabled FROM smartregression.web_users WHERE id=:owner FOR UPDATE",
            owner=owner,
        ).first()
        if row is None or not row.enabled:
            raise AuthFailure("invalid_session", 401)
        if not row.verified:
            raise AuthFailure("email_verification_required", 403)

    def active_count(self, owner):
        return self.execute(
            "SELECT count(*) FROM smartregression.web_projects "
            "WHERE owner_id=:owner AND NOT archived",
            owner=owner,
        ).scalar_one()

    @staticmethod
    def project(row):
        if row is None:
            raise AuthFailure("project_not_found", 404)
        return Project.model_validate({k: v for k, v in row.items() if k != "owner_id"})

    def get(self, owner, project, *, lock=False):
        row = (
            self.execute(
                "SELECT * FROM smartregression.web_projects WHERE owner_id=:owner AND id=:id"
                + (" FOR UPDATE" if lock else ""),
                owner=owner,
                id=project,
            )
            .mappings()
            .first()
        )
        return self.project(row)

    def create(self, owner, identity, body):
        # Project registration authorizes the GitHub identity before report publication.
        slug = body.repository_url.removeprefix("https://github.com/").lower()
        repository_id = "github-" + hashlib.sha256(slug.encode()).hexdigest()
        self.execute(
            "INSERT INTO smartregression.repositories(repository_id,source_kind) "
            "VALUES(:id,'github') ON CONFLICT(repository_id) DO NOTHING",
            id=repository_id,
        )
        kind = self.execute(
            "SELECT source_kind FROM smartregression.repositories WHERE repository_id=:id",
            id=repository_id,
        ).scalar_one()
        if kind != "github":
            raise AuthFailure("repository_identity_conflict", 409)
        row = (
            self.execute(
                "INSERT INTO smartregression.web_projects"
                "(id,owner_id,title,description,repository_url) "
                "VALUES(:id,:owner,:title,:description,:url) RETURNING *",
                id=identity,
                owner=owner,
                title=body.title,
                description=body.description,
                url=body.repository_url,
            )
            .mappings()
            .one()
        )
        return self.project(row)

    def update(self, owner, identity, body):
        row = (
            self.execute(
                "UPDATE smartregression.web_projects SET title=:title,description=:description,"
                "version=version+1,updated_at=CURRENT_TIMESTAMP "
                "WHERE owner_id=:owner AND id=:id RETURNING *",
                owner=owner,
                id=identity,
                title=body.title,
                description=body.description,
            )
            .mappings()
            .first()
        )
        return self.project(row)

    def archive(self, owner, identity, archived):
        row = (
            self.execute(
                "UPDATE smartregression.web_projects SET archived=:archived,version=version+1,"
                "updated_at=CURRENT_TIMESTAMP WHERE owner_id=:owner AND id=:id RETURNING *",
                owner=owner,
                id=identity,
                archived=archived,
            )
            .mappings()
            .first()
        )
        return self.project(row)

    def list(self, owner, search, archived, cursor, limit):
        params = dict(owner=owner, search=search, archived=archived, limit=limit)
        clause = ""
        if cursor:
            clause = " AND (created_at,id)<(:stamp,CAST(:cursor_id AS uuid))"
            params.update(stamp=cursor[0], cursor_id=cursor[1])
        rows = self.execute(
            "SELECT * FROM smartregression.web_projects "
            "WHERE owner_id=:owner AND archived=:archived "
            "AND (strpos(lower(title),lower(:search))>0 OR "
            "strpos(lower(repository_url),lower(:search))>0)"
            + clause
            + " ORDER BY created_at DESC,id DESC LIMIT :limit",
            **params,
        ).mappings()
        return [self.project(row) for row in rows]

    def activity(self, owner, project, action, object_id):
        self.execute(
            "INSERT INTO smartregression.web_activity(id,owner_id,project_id,action,object_id) "
            "VALUES(:id,:owner,:project,:action,:object_id)",
            id=str(uuid4()),
            owner=owner,
            project=project,
            action=action,
            object_id=object_id,
        )

    def activities(self, owner, project, cursor, limit):
        params = dict(owner=owner, project=project, limit=limit)
        clause = ""
        if cursor:
            clause = " AND (created_at,id)<(:stamp,CAST(:cursor_id AS uuid))"
            params.update(stamp=cursor[0], cursor_id=cursor[1])
        rows = self.execute(
            "SELECT id,project_id,action,object_id,created_at FROM smartregression.web_activity "
            "WHERE owner_id=:owner AND project_id=:project"
            + clause
            + " ORDER BY created_at DESC,id DESC LIMIT :limit",
            **params,
        ).mappings()
        return [Activity.model_validate(row) for row in rows]

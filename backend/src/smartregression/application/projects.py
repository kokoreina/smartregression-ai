"""Owner-scoped project use cases; persistence and remote verification are ports."""

import base64
import json
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from smartregression.application.auth import AuthFailure
from smartregression.application.repository_errors import public_repository_error
from smartregression.contracts.projects import (
    Activity,
    ActivityPage,
    Project,
    ProjectCreate,
    ProjectPage,
    ProjectUpdate,
)


class ProjectTransaction(Protocol):
    def lock_owner(self, owner: str) -> None: ...
    def active_count(self, owner: str) -> int: ...
    def get(self, owner: str, project: str, *, lock: bool = False) -> Project: ...
    def create(self, owner: str, identity: str, body: ProjectCreate) -> Project: ...
    def update(self, owner: str, identity: str, body: ProjectUpdate) -> Project: ...
    def archive(self, owner: str, identity: str, archived: bool) -> Project: ...
    def list(
        self, owner: str, search: str, archived: bool, cursor: tuple | None, limit: int
    ) -> list[Project]: ...
    def activity(self, owner: str, project: str, action: str, object_id: str) -> None: ...
    def activities(
        self, owner: str, project: str, cursor: tuple | None, limit: int
    ) -> list[Activity]: ...


class ProjectStore(Protocol):
    def transaction(self) -> AbstractContextManager[ProjectTransaction]: ...


def decode_cursor(value: str | None) -> tuple | None:
    if value is None:
        return None
    try:
        if len(value) > 256:
            raise ValueError()
        stamp, identity = json.loads(base64.urlsafe_b64decode(value.encode()))
        parsed = datetime.fromisoformat(stamp)
        if parsed.tzinfo is None:
            raise ValueError()
        return parsed, str(UUID(identity))
    except ValueError, TypeError, UnicodeError:
        raise AuthFailure("invalid_cursor", 422) from None


def page_cursor(items: list, limit: int) -> str | None:
    if len(items) <= limit:
        return None
    last = items[limit - 1]
    return base64.urlsafe_b64encode(
        json.dumps([last.created_at.isoformat(), str(last.id)]).encode()
    ).decode()


class ProjectService:
    def __init__(
        self, store: ProjectStore, inspect: Callable[[str], object], tree: Callable | None = None
    ):
        self.store, self.inspect = store, inspect
        self.tree_reader = tree

    def repository(self, owner: str, identity: str):
        project = self.get(owner, identity)
        try:
            return self.inspect(project.repository_url)
        except (ValueError, KeyError, TypeError) as error:
            raise AuthFailure(
                public_repository_error(error, "repository_lookup_failed"), 422
            ) from None

    def tree(self, owner: str, identity: str, commit: str):
        from smartregression.contracts.repository import RepositoryTreeRequest

        project = self.get(owner, identity)
        if self.tree_reader is None:
            raise AuthFailure("repository_unavailable", 503)
        try:
            return self.tree_reader(
                RepositoryTreeRequest(repository_url=project.repository_url, commit=commit)
            )
        except (ValueError, KeyError, TypeError) as error:
            raise AuthFailure(
                public_repository_error(error, "repository_tree_failed"), 422
            ) from None

    def create(self, owner: str, body: ProjectCreate) -> Project:
        try:
            self.inspect(body.repository_url)
        except (ValueError, KeyError, TypeError) as error:
            raise AuthFailure(
                public_repository_error(error, "repository_lookup_failed"), 422
            ) from None
        with self.store.transaction() as tx:
            tx.lock_owner(owner)
            if tx.active_count(owner) >= 3:
                raise AuthFailure("active_project_limit", 409)
            result = tx.create(owner, str(uuid4()), body)
            tx.activity(owner, str(result.id), "project_created", str(result.id))
            return result

    def list(
        self,
        owner: str,
        search: str = "",
        archived: bool = False,
        cursor: str | None = None,
        limit: int = 25,
    ) -> ProjectPage:
        with self.store.transaction() as tx:
            items = tx.list(owner, search, archived, decode_cursor(cursor), limit + 1)
        return ProjectPage(items=items[:limit], next_cursor=page_cursor(items, limit))

    def get(self, owner: str, identity: str) -> Project:
        with self.store.transaction() as tx:
            return tx.get(owner, identity)

    def update(self, owner: str, identity: str, body: ProjectUpdate) -> Project:
        with self.store.transaction() as tx:
            tx.lock_owner(owner)
            current = tx.get(owner, identity, lock=True)
            if current.version != body.version:
                raise AuthFailure("version_conflict", 409)
            result = tx.update(owner, identity, body)
            tx.activity(owner, identity, "project_updated", identity)
            return result

    def archive(self, owner: str, identity: str, version: int, archived: bool) -> Project:
        with self.store.transaction() as tx:
            tx.lock_owner(owner)
            current = tx.get(owner, identity, lock=True)
            if current.version != version:
                raise AuthFailure("version_conflict", 409)
            if current.archived == archived:
                return current
            if not archived and tx.active_count(owner) >= 3:
                raise AuthFailure("active_project_limit", 409)
            result = tx.archive(owner, identity, archived)
            tx.activity(
                owner, identity, "project_archived" if archived else "project_restored", identity
            )
            return result

    def activity(
        self,
        owner: str,
        identity: str,
        cursor: str | None = None,
        limit: int = 25,
    ) -> ActivityPage:
        with self.store.transaction() as tx:
            tx.get(owner, identity)
            items = tx.activities(owner, identity, decode_cursor(cursor), limit + 1)
        return ActivityPage(items=items[:limit], next_cursor=page_cursor(items, limit))

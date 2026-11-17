"""Personal projects transport. Every nested operation checks the session owner."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from smartregression.api.project_dependencies import product_csrf, verified_owner
from smartregression.application.auth import AuthFailure, User
from smartregression.application.projects import ProjectService
from smartregression.contracts.projects import (
    ActivityPage,
    Project,
    ProjectCreate,
    ProjectPage,
    ProjectUpdate,
    ProjectVersion,
)

Owner = Annotated[User, Depends(verified_owner)]


def service(request: Request) -> ProjectService:
    current = getattr(request.app.state, "project_service", None)
    if current is None:
        raise AuthFailure("project_storage_unavailable", 503)
    return current


def project_router() -> APIRouter:
    from smartregression.contracts.repository import RepositoryOverview, RepositoryTree

    router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
    Service = Annotated[ProjectService, Depends(service)]

    @router.get("", response_model=ProjectPage)
    def listing(
        user: Owner,
        projects: Service,
        search: str = Query("", max_length=120),
        archived: bool = False,
        cursor: str | None = Query(None, max_length=256),
        limit: int = Query(25, ge=1, le=100),
    ):
        return projects.list(user.id, search, archived, cursor, limit)

    @router.post("", response_model=Project, status_code=201, dependencies=[Depends(product_csrf)])
    def create(body: ProjectCreate, user: Owner, projects: Service):
        return projects.create(user.id, body)

    @router.get("/{project_id}", response_model=Project)
    def detail(project_id: UUID, user: Owner, projects: Service):
        return projects.get(user.id, str(project_id))

    @router.patch("/{project_id}", response_model=Project, dependencies=[Depends(product_csrf)])
    def update(project_id: UUID, body: ProjectUpdate, user: Owner, projects: Service):
        return projects.update(user.id, str(project_id), body)

    @router.post(
        "/{project_id}/archive", response_model=Project, dependencies=[Depends(product_csrf)]
    )
    def archive(project_id: UUID, body: ProjectVersion, user: Owner, projects: Service):
        return projects.archive(user.id, str(project_id), body.version, True)

    @router.post(
        "/{project_id}/restore", response_model=Project, dependencies=[Depends(product_csrf)]
    )
    def restore(project_id: UUID, body: ProjectVersion, user: Owner, projects: Service):
        return projects.archive(user.id, str(project_id), body.version, False)

    @router.get("/{project_id}/activity", response_model=ActivityPage)
    def activity(
        project_id: UUID,
        user: Owner,
        projects: Service,
        cursor: str | None = Query(None, max_length=256),
        limit: int = Query(25, ge=1, le=100),
    ):
        return projects.activity(user.id, str(project_id), cursor, limit)

    @router.get("/{project_id}/repository", response_model=RepositoryOverview)
    def repository(project_id: UUID, user: Owner, projects: Service):
        return projects.repository(user.id, str(project_id))

    @router.get("/{project_id}/tree", response_model=RepositoryTree)
    def tree(
        project_id: UUID,
        user: Owner,
        projects: Service,
        commit: str = Query(pattern="^[0-9a-f]{40}$"),
    ):
        return projects.tree(user.id, str(project_id), commit)

    return router

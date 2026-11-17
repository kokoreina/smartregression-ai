"""Notes/pins and resumable state share the authenticated project boundary."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from smartregression.api.project_dependencies import product_csrf, verified_owner
from smartregression.application.auth import AuthFailure, User
from smartregression.application.notes import NoteService
from smartregression.contracts.notes import (
    Note,
    NoteCreate,
    NotePage,
    NoteUpdate,
    ViewState,
    ViewStateInput,
)

Owner = Annotated[User, Depends(verified_owner)]


def service(request: Request) -> NoteService:
    value = getattr(request.app.state, "note_service", None)
    if value is None:
        raise AuthFailure("notes_unavailable", 503)
    return value


Service = Annotated[NoteService, Depends(service)]


def note_router():
    router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["notes and resume"])

    @router.post(
        "/notes", response_model=Note, status_code=201, dependencies=[Depends(product_csrf)]
    )
    def create(project_id: UUID, body: NoteCreate, user: Owner, notes: Service):
        return notes.create(user.id, str(project_id), body)

    @router.patch("/notes/{note_id}", response_model=Note, dependencies=[Depends(product_csrf)])
    def update(project_id: UUID, note_id: UUID, body: NoteUpdate, user: Owner, notes: Service):
        return notes.update(user.id, str(project_id), str(note_id), body)

    @router.get("/notes", response_model=NotePage)
    def listing(
        project_id: UUID,
        user: Owner,
        notes: Service,
        cursor: str | None = Query(None, max_length=256),
        limit: int = Query(25, ge=1, le=100),
        current: str | None = Query(None, pattern="^[0-9a-f]{40}$"),
    ):
        return notes.store.list(user.id, str(project_id), cursor, limit, current)

    @router.get("/view-state", response_model=ViewState | None)
    def view(project_id: UUID, user: Owner, notes: Service):
        return notes.store.view(user.id, str(project_id))

    @router.put("/view-state", response_model=ViewState, dependencies=[Depends(product_csrf)])
    def save(project_id: UUID, body: ViewStateInput, user: Owner, notes: Service):
        return notes.store.save_view(user.id, str(project_id), body)

    return router

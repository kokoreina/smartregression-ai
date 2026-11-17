"""Validated business notes and explicit resume-state persistence."""

from typing import Protocol

from smartregression.application.auth import AuthFailure
from smartregression.contracts.notes import (
    Note,
    NoteCreate,
    NotePage,
    NoteUpdate,
    ViewState,
    ViewStateInput,
)
from smartregression.core.retrieval.exclusions import contains_recognized_secret


class NoteStore(Protocol):
    def create(self, owner: str, project: str, body: NoteCreate) -> Note: ...
    def update(self, owner: str, project: str, identity: str, body: NoteUpdate) -> Note: ...
    def list(
        self, owner: str, project: str, cursor: str | None, limit: int, current: str | None
    ) -> NotePage: ...
    def view(self, owner: str, project: str) -> ViewState | None: ...
    def save_view(self, owner: str, project: str, body: ViewStateInput) -> ViewState: ...


class NoteService:
    def __init__(self, store: NoteStore):
        self.store = store

    @staticmethod
    def content(body: NoteCreate | NoteUpdate) -> None:
        if not body.title.strip() or contains_recognized_secret(body.title + "\n" + body.body):
            raise AuthFailure("note_content_rejected", 422)

    def create(self, owner: str, project: str, body: NoteCreate) -> Note:
        self.content(body)
        return self.store.create(owner, project, body)

    def update(self, owner: str, project: str, identity: str, body: NoteUpdate) -> Note:
        self.content(body)
        return self.store.update(owner, project, identity, body)

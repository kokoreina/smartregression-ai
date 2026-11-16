"""Notes/pins are business records; explorer view state contains no AI draft."""

from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field

from smartregression.contracts.repository import GitHubCommit as Commit
from smartregression.contracts.repository import WebValue
from smartregression.contracts.stages import RepoPath


class NoteCreate(WebValue):
    kind: Literal["note", "pin"] = "note"
    commit: Commit
    path: RepoPath
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(default="", max_length=10000)


class NoteUpdate(WebValue):
    version: int = Field(ge=1, strict=True)
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(default="", max_length=10000)
    archived: bool = False


class Note(NoteCreate):
    id: UUID
    version: int
    archived: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime
    stale: bool | None = None


class NotePage(WebValue):
    items: list[Note]
    next_cursor: str | None = None


class ViewStateInput(WebValue):
    version: int = Field(ge=0, strict=True)
    commit: Commit
    path: RepoPath | None = None
    tab: Literal["tree", "graph", "details"] = "graph"
    expanded_paths: list[RepoPath] = Field(default_factory=list, max_length=1000)
    focus_only: bool = False


class ViewState(ViewStateInput):
    updated_at: AwareDatetime
    stale: bool | None = None

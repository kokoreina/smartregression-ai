"""Personal project contracts. Ownership is never accepted from a client."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, StringConstraints

from smartregression.contracts.repository import RepositoryLookup, WebValue

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class ProjectCreate(RepositoryLookup):
    title: Title
    description: str = Field(default="", max_length=2000)


class ProjectUpdate(WebValue):
    version: int = Field(ge=1, strict=True)
    title: Title
    description: str = Field(default="", max_length=2000)


class ProjectVersion(WebValue):
    version: int = Field(ge=1, strict=True)


class Project(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    id: UUID
    title: str
    description: str
    repository_url: str
    archived: bool
    version: int
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ProjectPage(WebValue):
    items: list[Project]
    next_cursor: str | None = None


class Activity(WebValue):
    id: UUID
    project_id: UUID
    action: str
    object_id: str
    created_at: AwareDatetime


class ActivityPage(WebValue):
    items: list[Activity]
    next_cursor: str | None = None

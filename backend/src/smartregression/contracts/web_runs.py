"""Versioned web lifecycle; canonical analysis stages remain unchanged."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, StringConstraints

from smartregression.contracts.repository import GitHubCommit as Commit
from smartregression.contracts.repository import RepositoryAnalysisResponse, WebValue

RunStatus = Literal["queued", "running", "completed", "failed", "interrupted"]


class RunCreate(WebValue):
    base: Commit
    target: Commit
    idempotency_key: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{8,100}$")]


class WebRun(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    id: UUID
    project_id: UUID
    repository_url: str
    base: Commit
    target: Commit
    config_digest: str
    status: RunStatus
    started_at: AwareDatetime
    finished_at: AwareDatetime | None
    error_code: str | None
    report_available: bool
    ai_status: Literal["not_run", "running", "completed", "failed"]


class RunPage(WebValue):
    items: list[WebRun]
    next_cursor: str | None = None


class SavedRunReport(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    run: WebRun
    payload: RepositoryAnalysisResponse


class AiRequest(WebValue):
    idempotency_key: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{8,100}$")]
    allow_metadata_egress: bool = False
    question: str = Field(default="Giải thích ảnh hưởng từ bằng chứng phân tích.", max_length=600)

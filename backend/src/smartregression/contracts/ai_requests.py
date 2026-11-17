"""AI reservation state is separate from static analysis and actual invoice cost."""

from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field

from smartregression.contracts.repository import NarrativeResult, WebValue


class AiJob(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    id: UUID
    run_id: UUID | None
    scope_key: str = ""
    context_hash: str | None = None
    provenance: dict = Field(default_factory=dict)
    status: Literal["queued", "running", "completed", "failed"]
    action: Literal["commit", "hypothesis", "reading_guide", "search", "file", "folder"]
    created_at: AwareDatetime
    finished_at: AwareDatetime | None
    result: NarrativeResult | None


class AiQuota(WebValue):
    granted_calls: int
    used_calls: int
    cap_micro_usd: int
    reserved_micro_usd: int
    known_actual_micro_usd: int
    unknown_actual_count: int


class ExcerptRange(WebValue):
    path: str = Field(min_length=1, max_length=2048)
    start: int = Field(ge=1)
    end: int = Field(ge=1)


class AssistanceAiRequest(WebValue):
    commit: str = Field(pattern="^[0-9a-f]{40}$")
    action: Literal["hypothesis", "reading_guide", "search", "file", "folder"]
    idempotency_key: str = Field(pattern="^[A-Za-z0-9_-]{8,100}$")
    question: str = Field(default="", max_length=600)
    path: str | None = Field(default=None, max_length=2048)
    scenario_id: UUID | None = None
    allow_metadata_egress: bool = False
    allow_excerpt_egress: bool = False
    excerpts: list[ExcerptRange] = Field(default_factory=list, max_length=5)

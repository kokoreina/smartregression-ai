"""Owner-scoped repository conversations and coalesced remote-change monitoring."""

import re
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, field_validator

from smartregression.contracts.ai_requests import AiJob, ExcerptRange
from smartregression.contracts.explorer import GraphCoverage, GraphEvidence
from smartregression.contracts.models import ChangedComponent
from smartregression.contracts.repository import GitHubCommit, WebValue
from smartregression.contracts.snapshots import SourceRange
from smartregression.core.git.snapshots import validate_snapshot_paths


class AssistantFact(WebValue):
    text: str
    evidence: list[GraphEvidence] = Field(default_factory=list, max_length=20)


class AssistantReply(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    commit: GitHubCommit
    kind: Literal["overview", "search", "changes", "no_evidence"]
    summary: str
    facts: list[AssistantFact] = Field(default_factory=list, max_length=24)
    coverage: GraphCoverage
    limitations: list[str]
    excerpts: list[SourceRange] = Field(default_factory=list, max_length=5)


class ThreadCreate(WebValue):
    commit: GitHubCommit
    title: str = Field(default="Hỏi về repository", min_length=1, max_length=120)
    idempotency_key: str = Field(pattern="^[A-Za-z0-9_-]{8,100}$")


class AssistantThread(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    id: UUID
    project_id: UUID
    commit: GitHubCommit
    config_digest: str
    title: str
    created_at: AwareDatetime


class MessageCreate(WebValue):
    idempotency_key: str = Field(pattern="^[A-Za-z0-9_-]{8,100}$")
    question: str = Field(min_length=1, max_length=600)
    action: Literal["chat", "overview", "changes"] = "chat"
    use_llm: bool = False
    allow_model_fallback: bool = False
    allow_metadata_egress: bool = False
    allow_excerpt_egress: bool = False
    excerpts: list[ExcerptRange] = Field(default_factory=list, max_length=5)


class AssistantMessage(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    id: UUID
    thread_id: UUID
    question: str
    reply: AssistantReply
    ai: AiJob | None = None
    created_at: AwareDatetime


class WatchInput(WebValue):
    branch: str = Field(min_length=1, max_length=200)
    paths: list[str] = Field(default_factory=list, max_length=20)
    automatic: bool = False
    interval_seconds: int = Field(default=600, ge=300, le=86400)
    version: int = Field(default=0, ge=0)

    @field_validator("branch")
    @classmethod
    def branch_name(cls, value):
        if (
            not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./-]{0,199}", value)
            or any(p in {"", ".", ".."} or p.endswith((".", ".lock")) for p in value.split("/"))
            or ".." in value
        ):
            raise ValueError("invalid_branch")
        return value

    @field_validator("paths")
    @classmethod
    def scope_paths(cls, value):
        for path in value:
            validate_snapshot_paths([path])
        return sorted(set(value))


class RepositoryWatch(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    branch: str
    paths: list[str]
    automatic: bool
    interval_seconds: int
    version: int
    last_commit: GitHubCommit
    checked_at: AwareDatetime | None
    next_check_at: AwareDatetime
    pending: bool
    error_code: str | None


class ScopeImpact(WebValue):
    path: str
    relationship: Literal["changed", "direct", "indirect"]
    chain: list[str] = Field(max_length=21)
    evidence: list[GraphEvidence] = Field(max_length=20)


class ChangeReport(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    base: GitHubCommit
    target: GitHubCommit
    config_digest: str
    branch: str
    changes: list[ChangedComponent] = Field(max_length=1000)
    scope: list[str]
    scope_impacts: list[ScopeImpact] = Field(max_length=150)
    impacts_truncated: bool
    base_coverage: GraphCoverage
    target_coverage: GraphCoverage
    limitations: list[str]


class ChangeNotification(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    id: UUID
    created_at: AwareDatetime
    read_at: AwareDatetime | None
    report: ChangeReport


class WebhookReceipt(WebValue):
    accepted: bool
    duplicate: bool
    scheduled: int

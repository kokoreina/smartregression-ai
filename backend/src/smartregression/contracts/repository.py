"""Additive local-web contracts; existing v1/v2/v3 reports remain unchanged."""

import hashlib
import re
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from smartregression.contracts.models import Commit
from smartregression.contracts.stages import RepoPath, StageAnalysisReport
from smartregression.contracts.workflow import ProviderError, ProviderUsage

BoundedText = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
GitHubCommit = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]


class WebValue(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RepositoryLookup(WebValue):
    repository_url: str = Field(min_length=1, max_length=240)

    @field_validator("repository_url")
    @classmethod
    def github_public_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            value != value.strip()
            or parsed.scheme != "https"
            or parsed.netloc != "github.com"
            or parsed.query
            or parsed.fragment
            or not re.fullmatch(
                r"/[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}/?", parsed.path
            )
        ):
            raise ValueError("public_github_url_required")
        owner, name = parsed.path.strip("/").split("/")
        name = name.removesuffix(".git")
        if name in {"", ".", ".."} or any(ord(c) < 32 for c in value):
            raise ValueError("public_github_url_required")
        return f"https://github.com/{owner}/{name}"


class RepositoryCommit(WebValue):
    sha: Commit
    message: str = Field(max_length=300)
    date: str = Field(max_length=40)


class RepositoryOverview(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    repository_url: str
    full_name: str
    default_branch: str
    commits: list[RepositoryCommit] = Field(max_length=10)


class RepositoryTreeRequest(RepositoryLookup):
    commit: Commit


class RepositoryTreeEntry(WebValue):
    path: str = Field(min_length=1, max_length=2048)
    kind: Literal["directory", "file", "symlink", "submodule"]
    size: int | None = Field(default=None, ge=0, le=9_007_199_254_740_991, strict=True)

    @field_validator("path")
    @classmethod
    def display_path(cls, value: str) -> str:
        # Metadata is displayed, never materialized on the host filesystem.
        parts = value.split("/")
        if (
            len(parts) > 40
            or any(p in {"", ".", ".."} for p in parts)
            or "\\" in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
        ):
            raise ValueError("invalid_tree_path")
        return value

    @model_validator(mode="after")
    def consistent_size(self) -> Self:
        if (self.kind in {"file", "symlink"}) != (self.size is not None):
            raise ValueError("invalid_tree_size")
        return self


class RepositoryTree(RepositoryTreeRequest):
    schema_version: Literal["1.0.0"] = "1.0.0"
    tree_sha: Commit
    entries: list[RepositoryTreeEntry] = Field(max_length=5000)

    @model_validator(mode="after")
    def consistent_hierarchy(self) -> Self:
        paths = {e.path: e.kind for e in self.entries}
        if len(paths) != len(self.entries):
            raise ValueError("duplicate_tree_path")
        for entry in self.entries:
            parent = entry.path.rpartition("/")[0]
            if parent and paths.get(parent) != "directory":
                raise ValueError("invalid_tree_parent")
        return self


class RepositoryAnalysisRequest(RepositoryLookup):
    base: Commit
    target: Commit
    use_llm: bool = True
    allow_metadata_egress: bool = False
    question: str = Field(
        default="Giải thích cấu trúc dự án và ảnh hưởng của các file thay đổi.", max_length=600
    )

    @model_validator(mode="after")
    def egress_authorized(self) -> Self:
        if self.use_llm and not self.allow_metadata_egress:
            raise ValueError("metadata_egress_consent_required")
        return self


class RepositoryFinding(WebValue):
    path: BoundedText
    explanation: BoundedText
    evidence_ids: list[BoundedText] = Field(min_length=1, max_length=8)


class NarrativeEvidence(WebValue):
    id: str
    path: RepoPath
    change: str | None = None
    symbol: str | None = None
    imports: RepoPath | None = None
    relationship: str | None = None
    explanation: str | None = None


class RepositoryExplanation(WebValue):
    summary: BoundedText
    findings: list[RepositoryFinding] = Field(max_length=12)
    limitations: list[BoundedText] = Field(max_length=8)


class NarrativeResult(WebValue):
    status: Literal["not_run", "completed", "failed"]
    data: RepositoryExplanation | None = None
    model: str | None = None
    error_code: ProviderError | None = None
    reason: str | None = None
    usage: ProviderUsage | None = None
    prompt_sha256: str | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.status == "completed" and (
            self.data is None or self.error_code is not None or self.reason is not None
        ):
            raise ValueError("invalid_narrative_success")
        if self.status != "completed" and self.data is not None:
            raise ValueError("invalid_narrative_data")
        if self.status == "not_run" and self.error_code is not None:
            raise ValueError("invalid_narrative_not_run")
        if self.status == "failed" and (self.error_code is None or self.reason is not None):
            raise ValueError("invalid_narrative_failure")
        return self


class RepositoryAnalysisResponse(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    repository: RepositoryOverview
    files: list[str] = Field(max_length=1000)
    report: StageAnalysisReport
    narrative: NarrativeResult
    narrative_evidence: list[NarrativeEvidence] = Field(max_length=180)
    selection_status: Literal["not_run"] = "not_run"
    execution_status: Literal["not_run"] = "not_run"
    limitations: list[str]

    @model_validator(mode="after")
    def bound_narrative_references(self) -> Self:
        if self.report.data_kind == "real":
            canonical = RepositoryLookup(
                repository_url=self.repository.repository_url
            ).repository_url
            slug = canonical.removeprefix("https://github.com/").lower()
            expected = "github-" + hashlib.sha256(slug.encode()).hexdigest()
            if (
                self.repository.full_name.lower() != slug
                or self.report.identity.repository_id != expected
            ):
                raise ValueError("repository_identity_mismatch")
        if len(set(self.files)) != len(self.files):
            raise ValueError("duplicate_snapshot_file")
        evidence = {e.id: e.path for e in self.narrative_evidence}
        if len(evidence) != len(self.narrative_evidence):
            raise ValueError("duplicate_narrative_evidence")
        if self.narrative.data:
            for finding in self.narrative.data.findings:
                if len(set(finding.evidence_ids)) != len(finding.evidence_ids) or any(
                    evidence.get(e) != finding.path for e in finding.evidence_ids
                ):
                    raise ValueError("unknown_narrative_reference")
        return self


class RepositoryReportExport(WebValue):
    """Portable offline report; export time is not the analysis execution time."""

    report_kind: Literal["repository-analysis"] = "repository-analysis"
    schema_version: Literal["1.0.0"] = "1.0.0"
    exported_at: AwareDatetime
    payload: RepositoryAnalysisResponse

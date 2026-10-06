"""Canonical contracts. External code and retrieved text are untrusted data."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Commit = Annotated[str, StringConstraints(pattern=r"^([0-9a-f]{40}|[0-9a-f]{64})$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"


class CommitPair(Contract):
    base: Commit
    target: Commit


class AnalysisRequest(Contract):
    repository: Text
    commits: CommitPair


class ChangedComponent(Contract):
    path: Text
    symbol: Text | None = None
    change: Literal["added", "modified", "deleted", "renamed"]
    previous_path: Text | None = None


class EvidenceReference(Contract):
    id: Text
    commit: Commit
    path: Text
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    symbol: Text | None = None
    excerpt: Text | None = None

    @model_validator(mode="after")
    def ordered_lines(self) -> Self:
        if self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        return self


class ImpactFinding(Contract):
    id: Text
    component: ChangedComponent
    explanation: Text
    evidence_ids: list[Text] = Field(min_length=1)


class TestDecision(Contract):
    # Framework-native IDs, e.g. pytest nodeid, never display names alone.
    test_id: Text
    reason: Text
    evidence_ids: list[Text] = Field(default_factory=list)


class TestSelection(Contract):
    framework: Text
    selected: list[TestDecision]
    skipped: list[TestDecision]
    fallback_reason: Text | None = None

    @model_validator(mode="after")
    def unique_decisions(self) -> Self:
        ids = [item.test_id for item in self.selected + self.skipped]
        if len(ids) != len(set(ids)):
            raise ValueError("test IDs must be unique across selected and skipped")
        return self


class ExecutionResult(Contract):
    test_id: Text
    outcome: Literal["passed", "failed", "skipped", "error", "not_run"]
    duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    detail: Text | None = None
    # A failed test is an observation, never a confirmed fault label.


class AnalysisReport(Contract):
    report_id: Text
    data_kind: Literal["demo", "real"]
    repository: Text
    commits: CommitPair
    analysis_status: Literal["completed", "partial", "failed", "not_implemented"]
    findings: list[ImpactFinding]
    evidence: list[EvidenceReference]
    selection: TestSelection
    execution_status: Literal["not_run", "completed", "partial", "error"]
    execution_results: list[ExecutionResult]
    analysis_duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    llm_cost_usd: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    notes: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def consistent_references(self) -> Self:
        evidence_ids = {item.id for item in self.evidence}
        if len(evidence_ids) != len(self.evidence):
            raise ValueError("evidence IDs must be unique")
        if len({item.id for item in self.findings}) != len(self.findings):
            raise ValueError("finding IDs must be unique")
        for item in self.evidence:
            if item.commit not in (self.commits.base, self.commits.target):
                raise ValueError("evidence commit must belong to the report commit pair")
        for item in [*self.findings, *self.selection.selected, *self.selection.skipped]:
            if not set(item.evidence_ids) <= evidence_ids:
                raise ValueError("unknown evidence reference")
        selected = {item.test_id for item in self.selection.selected}
        result_ids = [item.test_id for item in self.execution_results]
        if len(result_ids) != len(set(result_ids)) or not set(result_ids) <= selected:
            raise ValueError("execution results must uniquely reference selected tests")
        if self.execution_status == "not_run" and self.execution_results:
            raise ValueError("not_run execution must have no results")
        if self.execution_status == "completed":
            if set(result_ids) != selected or any(
                item.outcome == "not_run" for item in self.execution_results
            ):
                raise ValueError("completed execution requires a result for each selected test")
        return self


class ErrorResponse(Contract):
    code: Text
    message: Text


class HealthResponse(Contract):
    status: Literal["ok"] = "ok"
    service: Literal["smartregression-api"] = "smartregression-api"
    scope: Literal["service_only"] = "service_only"

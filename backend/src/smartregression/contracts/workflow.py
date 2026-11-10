"""Versioned Sprint 3 values. Structural validity is not dispatch authorization."""

import hashlib
from typing import Literal, Self

from pydantic import Field, model_validator

from smartregression.contracts.models import Text
from smartregression.contracts.stages import (
    Code,
    Digest,
    EvidencePayload,
    InventoryPayload,
    NativeTestId,
    RetrievalItem,
    RetrievalPayload,
    RunIdentity,
    StageAnalysisReport,
    StageResult,
    StageValue,
    require_snapshot,
    unique,
)
from smartregression.core.git.snapshots import canonical_json


def inventory_fingerprint(value: InventoryPayload | dict) -> str:
    checked = InventoryPayload.model_validate(value)
    return hashlib.sha256(canonical_json(checked.model_dump(mode="json"))).hexdigest()


def context_fingerprint(value: RetrievalPayload | dict) -> str:
    checked = RetrievalPayload.model_validate(value)
    return hashlib.sha256(canonical_json(checked.model_dump(mode="json"))).hexdigest()


def evidence_fingerprint(value: EvidencePayload | dict) -> str:
    checked = EvidencePayload.model_validate(value)
    return hashlib.sha256(canonical_json(checked.model_dump(mode="json"))).hexdigest()


class ProposalProvenance(StageValue):
    identity: RunIdentity
    inventory_sha256: Digest
    context_sha256: Digest
    evidence_sha256: Digest
    prompt_version: Text
    configuration_id: Digest
    provider: Code
    model: Text

    @model_validator(mode="after")
    def materialized(self) -> Self:
        require_snapshot(self.identity.base)
        require_snapshot(self.identity.target)
        return self


class PromptContext(StageValue):
    """Authorized text supplied by application, never interpreted as policy."""

    reference: RetrievalItem
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def content_matches(self) -> Self:
        try:
            raw = self.text.encode("utf-8")
        except UnicodeError:
            raise ValueError("invalid_context_encoding") from None
        if len(raw) > 4096 or hashlib.sha256(raw).hexdigest() != self.reference.content_sha256:
            raise ValueError("context_content_mismatch_or_limit")
        return self


class ProposalRequest(StageValue):
    schema_version: Literal["3.0.0"]
    provenance: ProposalProvenance
    inventory: InventoryPayload
    retrieval: RetrievalPayload
    evidence: EvidencePayload
    context: list[PromptContext] = Field(max_length=16)

    @model_validator(mode="after")
    def bound_inputs(self) -> Self:
        provenance = self.provenance
        identity = provenance.identity
        if self.inventory.snapshot != identity.target or self.inventory.completeness != "complete":
            raise ValueError("complete_target_inventory_required")
        if any(s.snapshot not in (identity.base, identity.target) for s in self.retrieval.sources):
            raise ValueError("foreign_context_snapshot")
        if any(e.snapshot not in (identity.base, identity.target) for e in self.evidence.items):
            raise ValueError("foreign_evidence_snapshot")
        if [c.reference for c in self.context] != self.retrieval.items:
            raise ValueError("context_references_mismatch")
        if sum(len(c.text.encode("utf-8")) for c in self.context) > 32768:
            raise ValueError("context_total_limit")
        if (
            inventory_fingerprint(self.inventory) != provenance.inventory_sha256
            or context_fingerprint(self.retrieval) != provenance.context_sha256
            or evidence_fingerprint(self.evidence) != provenance.evidence_sha256
        ):
            raise ValueError("proposal_input_digest_mismatch")
        return self


class TestSuggestion(StageValue):
    test_id: NativeTestId
    reason: Text
    evidence_ids: list[Text] = Field(min_length=1)

    @model_validator(mode="after")
    def references(self) -> Self:
        unique(list(self.evidence_ids))
        return self


class TestProposal(StageValue):
    suggestions: list[TestSuggestion]

    @model_validator(mode="after")
    def identifiers(self) -> Self:
        unique([s.test_id for s in self.suggestions])
        return self


class ProviderUsage(StageValue):
    input_tokens: int | None = Field(default=None, ge=0, strict=True)
    output_tokens: int | None = Field(default=None, ge=0, strict=True)
    thinking_tokens: int | None = Field(default=None, ge=0, strict=True)
    total_tokens: int | None = Field(default=None, ge=0, strict=True)
    duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False, strict=True)
    cost_usd: float | None = Field(default=None, ge=0, allow_inf_nan=False, strict=True)


ProviderError = Literal[
    "provider_auth",
    "provider_permission",
    "provider_configuration",
    "provider_quota",
    "provider_rate_limit",
    "provider_timeout",
    "provider_transport",
    "provider_refusal",
    "provider_empty",
    "provider_truncated",
    "provider_invalid_output",
    "provider_budget",
]


class ProviderResult(StageValue):
    status: Literal["not_run", "completed", "failed"]
    provenance: ProposalProvenance | None = None
    data: TestProposal | None = None
    reason: Code | None = None
    error_code: ProviderError | None = None
    attempts: int = Field(default=0, ge=0, strict=True)
    usage: ProviderUsage | None = None
    actual_model_version: Text | None = None

    @model_validator(mode="after")
    def legal_state(self) -> Self:
        if self.status == "not_run":
            if (
                self.reason is None
                or self.error_code is not None
                or self.data is not None
                or self.provenance is not None
                or self.attempts != 0
                or self.usage is not None
                or self.actual_model_version is not None
            ):
                raise ValueError("invalid_provider_not_run")
        elif self.provenance is None or self.reason is not None:
            raise ValueError("provider_provenance_required")
        elif self.status == "completed":
            if self.data is None or self.error_code is not None or self.attempts < 1:
                raise ValueError("invalid_provider_success")
        elif self.data is not None or self.error_code is None:
            raise ValueError("invalid_provider_failure")
        return self


def validate_proposal_references(
    result: ProviderResult, inventory: InventoryPayload, evidence: EvidencePayload
) -> None:
    if result.data is None:
        return
    known_tests = set(inventory.test_ids)
    known_evidence = {e.id for e in evidence.items}
    for suggestion in result.data.suggestions:
        if suggestion.test_id not in known_tests:
            raise ValueError("unknown_proposed_test")
        if not set(suggestion.evidence_ids) <= known_evidence:
            raise ValueError("unknown_proposed_evidence")
    # Membership is not semantic support: 3.05 must still verify each suggestion.


class SelectionManifest(StageValue):
    manifest_id: Text
    identity: RunIdentity
    inventory: InventoryPayload
    inventory_sha256: Digest
    policy_version: Literal["s1-selection-v1"]
    configuration_id: Digest
    mode: Literal["hybrid", "dependency_fallback", "full_suite", "no_tests"]
    selected: list[NativeTestId]
    not_selected: list[NativeTestId]
    reason: Code

    @model_validator(mode="after")
    def partition(self) -> Self:
        require_snapshot(self.identity.base)
        require_snapshot(self.identity.target)
        if (
            self.inventory.snapshot != self.identity.target
            or self.inventory.completeness != "complete"
        ):
            raise ValueError("complete_target_inventory_required")
        if inventory_fingerprint(self.inventory) != self.inventory_sha256:
            raise ValueError("inventory_digest_mismatch")
        unique(list(self.selected) + list(self.not_selected))
        target = self.inventory.test_ids
        selected = set(self.selected)
        unselected = set(self.not_selected)
        if selected | unselected != set(target):
            raise ValueError("inventory_partition_mismatch")
        if self.selected != [t for t in target if t in selected] or self.not_selected != [
            t for t in target if t in unselected
        ]:
            raise ValueError("inventory_order_mismatch")
        if (self.mode == "no_tests") != (not target):
            raise ValueError("invalid_no_tests_mode")
        if target and not self.selected or self.mode == "full_suite" and self.not_selected:
            raise ValueError("unsafe_empty_or_incomplete_full_suite")
        return self


class TestObservation(StageValue):
    test_id: NativeTestId
    outcome: Literal["passed", "failed", "skipped", "error"]
    duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False, strict=True)


class ExecutionPayload(StageValue):
    identity: RunIdentity
    manifest_id: Text
    dispatched_test_ids: list[NativeTestId]
    observations: list[TestObservation]
    termination: Literal["exited", "timeout", "cancelled", "infrastructure_error", "output_limit"]

    @model_validator(mode="after")
    def observations_match(self) -> Self:
        require_snapshot(self.identity.base)
        require_snapshot(self.identity.target)
        unique(list(self.dispatched_test_ids))
        observed = [o.test_id for o in self.observations]
        unique(list(observed))
        if not set(observed) <= set(self.dispatched_test_ids):
            raise ValueError("undispatched_test_observation")
        if self.termination == "exited" and set(observed) != set(self.dispatched_test_ids):
            raise ValueError("missing_test_observations")
        return self


class WorkflowReport(StageValue):
    """v3 envelope preserves the complete v2 analysis without fake later stages."""

    schema_version: Literal["3.0.0"]
    analysis: StageAnalysisReport
    proposal: ProviderResult
    selection: StageResult[SelectionManifest]
    execution: StageResult[ExecutionPayload]

    @property
    def data_kind(self) -> str:
        return self.analysis.data_kind

    @property
    def report_id(self) -> str:
        return self.analysis.report_id

    @model_validator(mode="after")
    def coherent_workflow(self) -> Self:
        analysis = self.analysis
        inventory = analysis.stages.inventory.data
        provenance = self.proposal.provenance
        if provenance is not None:
            retrieval = analysis.stages.retrieval.data
            evidence = analysis.stages.evidence.data
            if (
                provenance.identity != analysis.identity
                or inventory is None
                or retrieval is None
                or evidence is None
                or analysis.stages.inventory.status != "completed"
                or inventory.completeness != "complete"
                or provenance.inventory_sha256 != inventory_fingerprint(inventory)
                or provenance.context_sha256 != context_fingerprint(retrieval)
                or provenance.evidence_sha256 != evidence_fingerprint(evidence)
            ):
                raise ValueError("proposal_provenance_mismatch")
            validate_proposal_references(self.proposal, inventory, evidence)
        manifest = self.selection.data
        if manifest is not None and (
            self.selection.status != "completed"
            or manifest.identity != analysis.identity
            or inventory is None
            or manifest.inventory != inventory
            or analysis.stages.inventory.status != "completed"
        ):
            raise ValueError("selection_manifest_mismatch")
        execution = self.execution.data
        if execution is not None:
            if (
                manifest is None
                or manifest.mode == "no_tests"
                or execution.identity != analysis.identity
                or execution.manifest_id != manifest.manifest_id
                or not set(execution.dispatched_test_ids) <= set(manifest.selected)
                or execution.dispatched_test_ids
                != [t for t in manifest.selected if t in execution.dispatched_test_ids]
            ):
                raise ValueError("execution_manifest_mismatch")
            if self.execution.status == "completed" and (
                execution.termination != "exited"
                or execution.dispatched_test_ids != manifest.selected
            ):
                raise ValueError("incomplete_execution")
            if self.execution.status == "partial" and execution.termination == "exited":
                raise ValueError("partial_execution_requires_termination")
        return self

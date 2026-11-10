"""Sprint 3 boundaries: proposals are not selection or execution authority."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from smartregression.application.proposals import ProposalBoundaryError, request_proposal
from smartregression.application.reports import validate_report_json
from smartregression.contracts.workflow import (
    ExecutionPayload,
    ProposalRequest,
    ProviderResult,
    SelectionManifest,
    WorkflowReport,
    context_fingerprint,
    evidence_fingerprint,
    inventory_fingerprint,
)

ROOT = Path(__file__).resolve().parents[3]


def request_data():
    analysis = json.loads((ROOT / "examples/reports/stage-report.partial.json").read_text())
    identity = analysis["identity"]
    inventory = dict(
        snapshot=identity["target"],
        framework="pytest",
        test_ids=["test_a", " test_b "],
        completeness="complete",
    )
    retrieval = dict(
        sources=[dict(snapshot=identity["target"], index_id="index", configuration_id="config")],
        items=[],
    )
    evidence = dict(items=[])
    return dict(
        schema_version="3.0.0",
        provenance=dict(
            identity=identity,
            inventory_sha256=inventory_fingerprint(inventory),
            context_sha256=context_fingerprint(retrieval),
            evidence_sha256=evidence_fingerprint(evidence),
            prompt_version="proposal/1",
            configuration_id="c" * 64,
            provider="gemini",
            model="configured-model",
        ),
        inventory=inventory,
        retrieval=retrieval,
        evidence=evidence,
        context=[],
    )


def result_data(request=None):
    request = request or request_data()
    return dict(
        status="completed", provenance=request["provenance"], attempts=1, data=dict(suggestions=[])
    )


def manifest_data():
    request = request_data()
    return dict(
        manifest_id="d" * 64,
        identity=request["provenance"]["identity"],
        inventory=request["inventory"],
        inventory_sha256=request["provenance"]["inventory_sha256"],
        policy_version="s1-selection-v1",
        configuration_id="e" * 64,
        mode="hybrid",
        selected=["test_a"],
        not_selected=[" test_b "],
        reason="policy_applied",
    )


def workflow_data():
    data = request_data()
    analysis = json.loads((ROOT / "examples/reports/stage-report.partial.json").read_text())
    for name in ["inventory", "retrieval", "evidence"]:
        analysis["stages"][name] = dict(status="completed", data=data[name])
    # This fixture's impact references its existing evidence; keep its source stages
    # inactive rather than manufacturing support for the request's empty evidence.
    for name in ["impact", "review_ordering"]:
        analysis["stages"][name] = dict(status="not_run", reason="fixture_not_run")
    return dict(
        schema_version="3.0.0",
        analysis=analysis,
        proposal=result_data(data),
        selection=dict(status="not_run", reason="selection_not_run"),
        execution=dict(status="not_run", reason="execution_not_run"),
    )


def test_proposal_only_report_is_read_without_fake_selection():
    report = validate_report_json(json.dumps(workflow_data()))
    assert isinstance(report, WorkflowReport)
    assert report.selection.data is None and report.execution.data is None
    assert report.proposal.usage is None
    assert report.data_kind == "demo" and report.schema_version == "3.0.0"


@pytest.mark.parametrize("field", ["extra", "fault_labels", "full_suite_outcomes", "api_key"])
def test_request_forbids_unrecognized_inputs(field):
    data = request_data()
    data[field] = "private-input-do-not-echo"
    with pytest.raises(ValidationError):
        ProposalRequest.model_validate(data)


@pytest.mark.parametrize("field", ["inventory_sha256", "context_sha256", "evidence_sha256"])
def test_request_fingerprints_cannot_relabel_input(field):
    data = request_data()
    data["provenance"][field] = "0" * 64
    with pytest.raises(ValidationError):
        ProposalRequest.model_validate(data)


@pytest.mark.parametrize(
    "field,value", [("completeness", "partial"), ("test_ids", ["test_a", "test_a"])]
)
def test_request_needs_complete_unique_target_inventory(field, value):
    data = request_data()
    data["inventory"][field] = value
    with pytest.raises(ValidationError):
        ProposalRequest.model_validate(data)


@pytest.mark.parametrize(
    "status,kwargs",
    [
        ("completed", {}),
        ("failed", {"error_code": "provider_auth"}),
        ("not_run", {"reason": "provider_not_run"}),
    ],
)
def test_provider_states_have_honest_measurements(status, kwargs):
    data = result_data()
    data.update(status=status, **kwargs)
    if status != "completed":
        data.pop("data")
    if status == "not_run":
        data.pop("provenance")
        data["attempts"] = 0
    result = ProviderResult.model_validate(data)
    assert result.usage is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(status="failed"),
        lambda d: d.update(error_code="provider_auth"),
        lambda d: d.update(provenance=None),
        lambda d: d.update(usage={"input_tokens": -1}),
        lambda d: d.update(usage={"input_tokens": True}),
        lambda d: d.update(usage={"cost_usd": float("nan")}),
        lambda d: d["data"].update(
            suggestions=[dict(test_id="test_a", reason="candidate", evidence_ids=[])]
        ),
    ],
)
def test_provider_invalid_states_rejected(mutate):
    data = result_data()
    mutate(data)
    with pytest.raises(ValidationError):
        ProviderResult.model_validate(data)


def test_native_id_is_preserved_and_duplicates_rejected():
    data = result_data()
    suggestion = dict(test_id=" test_b ", reason="candidate", evidence_ids=["evidence-1"])
    data["data"]["suggestions"] = [suggestion]
    assert ProviderResult.model_validate(data).data.suggestions[0].test_id == " test_b "
    data["data"]["suggestions"].append(deepcopy(suggestion))
    with pytest.raises(ValidationError):
        ProviderResult.model_validate(data)


class FakeProvider:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def propose(self, request):
        self.calls += 1
        return self.result


def test_real_application_boundary_uses_typed_fake_once():
    request = ProposalRequest.model_validate(request_data())
    provider = FakeProvider(ProviderResult.model_validate(result_data()))
    result = request_proposal(provider, request)
    assert result.status == "completed" and provider.calls == 1


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("identity", "proposal_provenance_mismatch"),
        ("test_id", "unknown_proposed_test"),
        ("evidence", "unknown_proposed_evidence"),
        ("malformed", "invalid_provider_output"),
    ],
)
def test_application_rejects_foreign_or_unknown_provider_output(mutation, code):
    data = result_data()
    if mutation == "identity":
        data["provenance"]["identity"]["run_id"] = "foreign"
    elif mutation in {"test_id", "evidence"}:
        data["data"]["suggestions"] = [
            dict(
                test_id="unknown" if mutation == "test_id" else "test_a",
                reason="candidate",
                evidence_ids=["unknown"],
            )
        ]
    provider = FakeProvider(
        data if mutation == "malformed" else ProviderResult.model_validate(data)
    )
    with pytest.raises(ProposalBoundaryError, match=code):
        request_proposal(provider, ProposalRequest.model_validate(request_data()))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["selected"].append("unknown"),
        lambda d: d.update(not_selected=[]),
        lambda d: d.update(not_selected=["test_a"]),
        lambda d: d.update(selected=[], not_selected=["test_a", " test_b "]),
        lambda d: d.update(mode="no_tests"),
        lambda d: d["identity"]["target"].update(commit="0" * 40),
        lambda d: d.update(inventory_sha256="0" * 64),
    ],
)
def test_manifest_rejects_incoherent_partition_and_identity(mutate):
    data = manifest_data()
    mutate(data)
    with pytest.raises(ValidationError):
        SelectionManifest.model_validate(data)


def test_manifest_partition_keeps_target_inventory_order():
    data = manifest_data()
    data.update(selected=["test_a", " test_b "], not_selected=[])
    assert SelectionManifest.model_validate(data).selected == ["test_a", " test_b "]
    data["selected"].reverse()
    with pytest.raises(ValidationError):
        SelectionManifest.model_validate(data)


def test_execution_is_bound_to_manifest_and_failure_is_not_a_fault_label():
    data = workflow_data()
    manifest = manifest_data()
    data["selection"] = dict(status="completed", data=manifest)
    data["execution"] = dict(
        status="completed",
        data=dict(
            identity=manifest["identity"],
            manifest_id=manifest["manifest_id"],
            dispatched_test_ids=["test_a"],
            termination="exited",
            observations=[dict(test_id="test_a", outcome="failed")],
        ),
    )
    report = WorkflowReport.model_validate(data)
    assert report.execution.data.observations[0].duration_seconds is None
    assert "fault_detected" not in report.model_dump_json()
    data["execution"]["data"]["manifest_id"] = "0" * 64
    with pytest.raises(ValidationError):
        WorkflowReport.model_validate(data)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["proposal"]["provenance"].update(context_sha256="0" * 64),
        lambda d: d["proposal"]["provenance"]["identity"].update(run_id="other"),
        lambda d: d.update(schema_version="3.1.0"),
        lambda d: d.pop("schema_version"),
        lambda d: d.update(
            selection=dict(status="completed", data=manifest_data()),
            execution=dict(status="completed", data=None),
        ),
    ],
)
def test_workflow_rejects_incoherent_nested_state(mutate):
    data = workflow_data()
    mutate(data)
    with pytest.raises(ValidationError):
        WorkflowReport.model_validate(data)


def test_v2_reader_cannot_silently_consume_v3():
    from smartregression.contracts.stages import StageAnalysisReport

    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(workflow_data())


def test_execution_rejects_duplicate_dispatch_or_foreign_observation():
    data = dict(
        identity=manifest_data()["identity"],
        manifest_id="d" * 64,
        dispatched_test_ids=["test_a"],
        observations=[dict(test_id="other", outcome="passed")],
        termination="exited",
    )
    with pytest.raises(ValidationError):
        ExecutionPayload.model_validate(data)


def test_provider_cannot_relabel_request_by_mutating_child_models():
    class MutatingProvider:
        def propose(self, request):
            request.provenance.identity.__dict__["run_id"] = "foreign-run"
            result = result_data()
            result["provenance"] = request.provenance.model_dump(mode="json")
            return ProviderResult.model_validate(result)

    with pytest.raises(ProposalBoundaryError, match="proposal_provenance_mismatch"):
        request_proposal(MutatingProvider(), ProposalRequest.model_validate(request_data()))


def test_context_text_is_bound_to_frozen_retrieval_metadata():
    data = request_data()
    item = dict(
        **data["retrieval"]["sources"][0],
        id="chunk-1",
        path="src/a.py",
        location=dict(line_start=1, line_end=1),
        rank=1,
        content_sha256=hashlib.sha256(b"value = 1\n").hexdigest(),
    )
    data["retrieval"]["items"] = [item]
    data["provenance"]["context_sha256"] = context_fingerprint(data["retrieval"])
    data["context"] = [dict(reference=item, text="value = 1\n")]
    assert ProposalRequest.model_validate(data).context[0].text == "value = 1\n"
    data["context"][0]["text"] = "changed"
    with pytest.raises(ValidationError):
        ProposalRequest.model_validate(data)


@pytest.mark.parametrize("field", ["base", "target"])
def test_foreign_request_snapshots_are_rejected(field):
    data = request_data()
    data["provenance"]["identity"][field]["repository_id"] = "foreign"
    with pytest.raises(ValidationError):
        ProposalRequest.model_validate(data)


def test_usage_zero_is_measured_and_missing_stays_null():
    data = result_data()
    data["usage"] = dict(cost_usd=0, input_tokens=0)
    usage = ProviderResult.model_validate(data).usage
    assert usage.cost_usd == 0 and usage.input_tokens == 0 and usage.output_tokens is None


@pytest.mark.parametrize("error_type", [RuntimeError, ProposalBoundaryError])
def test_unexpected_provider_exception_is_redacted(error_type):
    class BrokenProvider:
        def propose(self, request):
            raise error_type("private-source-marker")

    with pytest.raises(ProposalBoundaryError, match="invalid_provider_output") as caught:
        request_proposal(BrokenProvider(), ProposalRequest.model_validate(request_data()))
    assert "private-source-marker" not in str(caught.value)


def test_native_id_whitespace_mismatch_is_not_silently_normalized():
    data = result_data()
    data["data"]["suggestions"] = [dict(test_id="test_b", reason="candidate", evidence_ids=["e"])]
    with pytest.raises(ProposalBoundaryError, match="unknown_proposed_test"):
        request_proposal(
            FakeProvider(ProviderResult.model_validate(data)),
            ProposalRequest.model_validate(request_data()),
        )


def test_known_suggestion_membership_is_not_semantic_verification():
    data = request_data()
    data["evidence"]["items"] = [
        dict(
            id="e1",
            snapshot=data["provenance"]["identity"]["target"],
            path="src/a.py",
            location=dict(line_start=1, line_end=1),
        )
    ]
    data["provenance"]["evidence_sha256"] = evidence_fingerprint(data["evidence"])
    result = result_data(data)
    result["data"]["suggestions"] = [
        dict(test_id=" test_b ", reason="candidate", evidence_ids=["e1"])
    ]
    checked = request_proposal(
        FakeProvider(ProviderResult.model_validate(result)), ProposalRequest.model_validate(data)
    )
    assert checked.data.suggestions[0].test_id == " test_b "
    assert ProposalRequest.model_validate(data).evidence.items[0].support == "unverified"


def test_no_tests_manifest_does_not_allow_fake_completed_execution():
    data = workflow_data()
    manifest = manifest_data()
    manifest["inventory"]["test_ids"] = []
    manifest.update(
        mode="no_tests",
        selected=[],
        not_selected=[],
        inventory_sha256=inventory_fingerprint(manifest["inventory"]),
    )
    data["proposal"] = dict(status="not_run", reason="empty_inventory")
    data["analysis"]["stages"]["inventory"]["data"] = manifest["inventory"]
    data["selection"] = dict(status="completed", data=manifest)
    assert WorkflowReport.model_validate(data).selection.data.mode == "no_tests"
    data["execution"] = dict(
        status="completed",
        data=dict(
            identity=manifest["identity"],
            manifest_id=manifest["manifest_id"],
            dispatched_test_ids=[],
            observations=[],
            termination="exited",
        ),
    )
    with pytest.raises(ValidationError):
        WorkflowReport.model_validate(data)


def test_partial_runner_termination_retains_observations_and_limits():
    data = workflow_data()
    manifest = manifest_data()
    data["selection"] = dict(status="completed", data=manifest)
    data["execution"] = dict(
        status="partial",
        limitations=[dict(code="execution_timeout")],
        data=dict(
            identity=manifest["identity"],
            manifest_id=manifest["manifest_id"],
            dispatched_test_ids=["test_a"],
            observations=[],
            termination="timeout",
        ),
    )
    assert WorkflowReport.model_validate(data).execution.data.termination == "timeout"
    data["execution"]["status"] = "completed"
    data["execution"]["limitations"] = []
    with pytest.raises(ValidationError):
        WorkflowReport.model_validate(data)


def test_saved_valid_invalid_fixtures_are_checked_by_backend():
    for path in (ROOT / "examples/reports").glob("workflow-report.*.json"):
        assert isinstance(validate_report_json(path.read_text("utf-8")), WorkflowReport)
    ProposalRequest.model_validate_json(
        (ROOT / "examples/reports/proposal-request.demo.json").read_text("utf-8")
    )
    with pytest.raises(ValidationError):
        validate_report_json(
            (ROOT / "backend/tests/fixtures/workflow-invalid-state.json").read_text("utf-8")
        )


@pytest.mark.parametrize("count,size", [(1, 4097), (9, 4096), (17, 1)])
def test_context_representation_limits_reject_overflow(count, size):
    data = request_data()
    text = "x" * size
    items = [
        dict(
            **data["retrieval"]["sources"][0],
            id=f"chunk-{i}",
            path="src/a.py",
            location=dict(line_start=i + 1, line_end=i + 1),
            rank=i + 1,
            content_sha256=hashlib.sha256(text.encode()).hexdigest(),
        )
        for i in range(count)
    ]
    data["retrieval"]["items"] = items
    data["provenance"]["context_sha256"] = context_fingerprint(data["retrieval"])
    data["context"] = [dict(reference=item, text=text) for item in items]
    with pytest.raises(ValidationError):
        ProposalRequest.model_validate(data)


def test_input_mutation_is_rejected_before_calling_provider():
    request = ProposalRequest.model_validate(request_data())
    request.inventory.test_ids.append("unexpected")
    provider = FakeProvider(ProviderResult.model_validate(result_data()))
    with pytest.raises(ProposalBoundaryError, match="invalid_proposal_request"):
        request_proposal(provider, request)
    assert provider.calls == 0

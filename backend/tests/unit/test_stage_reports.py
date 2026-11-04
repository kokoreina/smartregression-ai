"""Public report behavior, including the legacy consumer boundary."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from smartregression.application.reports import validate_report_json
from smartregression.contracts.stages import EvidenceBundle, InventoryPayload, StageAnalysisReport


def empty_report() -> dict:
    base = {"repository_id": "demo-repo", "commit": "a" * 40, "snapshot_id": "1" * 64}
    target = {**base, "commit": "b" * 40, "snapshot_id": "2" * 64}
    return {
        "schema_version": "2.0.0",
        "report_id": "example-report",
        "data_kind": "demo",
        "identity": {
            "repository_id": "demo-repo",
            "run_id": "run-1",
            "base": base,
            "target": target,
            "comparison_mode": "direct_two_tree",
        },
        "analysis_status": "not_implemented",
        "stages": {
            name: {"status": "not_implemented", "reason": "producer_unavailable"}
            for name in (
                "snapshots",
                "changes",
                "graph",
                "impact",
                "inventory",
                "retrieval",
                "evidence",
                "review_ordering",
            )
        },
    }


def test_stage_report_validates_without_selection_or_execution() -> None:
    report = validate_report_json(json.dumps(empty_report()))
    assert report.schema_version == "2.0.0"
    assert "selection" not in report.model_dump()
    assert "execution_results" not in report.model_dump()


def test_old_report_still_uses_old_validation(demo_data: dict) -> None:
    report = validate_report_json(json.dumps(demo_data))
    assert report.schema_version == "1.0.0"
    assert report.selection.framework == demo_data["selection"]["framework"]


def test_empty_completed_stage_is_distinct_from_not_run() -> None:
    data = empty_report()
    data["analysis_status"] = "partial"
    data["stages"]["changes"] = {"status": "completed", "data": {"components": [], "files": []}}
    report = validate_report_json(json.dumps(data))
    assert report.stages.changes.data.components == []
    assert report.stages.impact.data is None


@pytest.mark.parametrize("mutation", ["unknown", "version", "identity", "status", "payload"])
def test_stage_report_rejects_inconsistent_envelopes(mutation: str) -> None:
    data = empty_report()
    if mutation == "unknown":
        data["selection"] = {"selected": [], "skipped": []}
    elif mutation == "version":
        data["schema_version"] = "3.0.0"
    elif mutation == "identity":
        data["identity"]["base"]["repository_id"] = "other-repo"
    elif mutation == "status":
        data["analysis_status"] = "completed"
    else:
        data["stages"]["changes"]["data"] = {"components": [], "files": []}
    with pytest.raises(ValidationError):
        validate_report_json(json.dumps(data))


def artifacts_report() -> dict:
    """Planned impact/evidence shape; does not claim a 2.04 producer exists."""
    data = empty_report()
    base, target = data["identity"]["base"], data["identity"]["target"]
    stages = data["stages"]
    stages["changes"] = {
        "status": "completed",
        "data": {
            "components": [
                {
                    "id": "changed",
                    "kind": "function",
                    "symbol": "f",
                    "path": "a.py",
                    "change": "modified",
                    "reason": "content_changed",
                    "base_location": {"line_start": 1, "line_end": 2},
                    "target_location": {"line_start": 1, "line_end": 2},
                }
            ],
            "files": [{"path": "a.py", "status": "completed", "limitations": []}],
        },
    }
    stages["graph"] = {
        "status": "completed",
        "data": {
            "snapshot": deepcopy(target),
            "nodes": ["a.py", "b.py", "c.py"],
            "edges": [
                {"source": "b.py", "target": "a.py", "kind": "absolute_import"},
                {"source": "c.py", "target": "b.py", "kind": "absolute_import"},
            ],
            "unresolved": [],
        },
    }
    stages["impact"] = {
        "status": "completed",
        "data": {
            "snapshot": deepcopy(target),
            "candidates": [
                {
                    "id": "candidate",
                    "path": "b.py",
                    "relationship": "direct",
                    "changed_component_id": "changed",
                    "path_ids": ["path-1"],
                    "evidence_ids": ["e-base", "e-target"],
                }
            ],
            "paths": [
                {"id": "path-1", "changed_component_id": "changed", "nodes": ["b.py", "a.py"]}
            ],
        },
    }
    stages["evidence"] = {
        "status": "partial",
        "limitations": [{"code": "not_verified"}],
        "data": {
            "items": [
                {
                    "id": "e-base",
                    "snapshot": deepcopy(base),
                    "path": "a.py",
                    "location": {"line_start": 1, "line_end": 2},
                },
                {
                    "id": "e-target",
                    "snapshot": deepcopy(target),
                    "path": "a.py",
                    "location": {"line_start": 1, "line_end": 2},
                },
            ]
        },
    }
    data["analysis_status"] = "partial"
    return data


def test_impact_paths_and_evidence_can_span_both_report_revisions() -> None:
    report = StageAnalysisReport.model_validate(artifacts_report())
    assert {e.snapshot.commit for e in report.stages.evidence.data.items} == {"a" * 40, "b" * 40}
    assert all(e.resolution == "unverified" for e in report.stages.evidence.data.items)
    bundle = EvidenceBundle(
        identity=report.identity,
        changes=report.stages.changes.data,
        graph=report.stages.graph.data,
        impact=report.stages.impact.data,
        evidence=report.stages.evidence.data,
    )
    assert EvidenceBundle.model_validate_json(bundle.model_dump_json()) == bundle


@pytest.mark.parametrize(
    "case",
    [
        "foreign_graph",
        "foreign_impact",
        "foreign_evidence",
        "unknown_component",
        "unknown_path",
        "unknown_evidence",
        "duplicate_component",
        "duplicate_path",
        "duplicate_evidence",
        "unknown_endpoint",
        "reverse_path",
        "missing_edge",
        "wrong_candidate",
        "wrong_relationship",
        "cycle",
        "unverified_completed",
        "unsupported_resolution",
        "location",
        "missing_symbol",
        "added_with_base",
        "deleted_with_target",
        "rename_without_previous",
        "absolute_path",
        "traversal",
        "invalid_commit",
        "missing_required",
        "extra_nested",
        "not_run_payload",
    ],
)
def test_rejects_unsafe_or_inconsistent_artifacts(case: str) -> None:
    data = artifacts_report()
    stages = data["stages"]
    changes, graph, impact, evidence = [
        stages[n]["data"] for n in ("changes", "graph", "impact", "evidence")
    ]
    c, p, candidate, e = (
        changes["components"][0],
        impact["paths"][0],
        impact["candidates"][0],
        evidence["items"][0],
    )
    match case:
        case "foreign_graph":
            graph["snapshot"]["repository_id"] = "foreign"
        case "foreign_impact":
            impact["snapshot"]["snapshot_id"] = "9" * 64
        case "foreign_evidence":
            e["snapshot"]["commit"] = "c" * 40
        case "unknown_component":
            p["changed_component_id"] = "unknown"
        case "unknown_path":
            candidate["path_ids"] = ["missing"]
        case "unknown_evidence":
            candidate["evidence_ids"] = ["missing"]
        case "duplicate_component":
            changes["components"].append(deepcopy(c))
        case "duplicate_path":
            impact["paths"].append(deepcopy(p))
        case "duplicate_evidence":
            evidence["items"].append(deepcopy(e))
        case "unknown_endpoint":
            graph["edges"][0]["source"] = "unknown.py"
        case "reverse_path":
            p["nodes"].reverse()
        case "missing_edge":
            graph["edges"] = []
        case "wrong_candidate":
            candidate["path"] = "c.py"
        case "wrong_relationship":
            candidate["relationship"] = "indirect"
        case "cycle":
            p["nodes"] = ["b.py", "a.py", "b.py", "a.py"]
        case "unverified_completed":
            stages["evidence"]["status"] = "completed"
        case "unsupported_resolution":
            e["support"] = "supported"
        case "location":
            e["location"]["line_end"] = 0
        case "missing_symbol":
            del c["symbol"]
        case "added_with_base":
            c["change"] = "added"
        case "deleted_with_target":
            c["change"] = "deleted"
        case "rename_without_previous":
            c["change"] = "renamed"
        case "absolute_path":
            e["path"] = "C:/private/a.py"
        case "traversal":
            e["path"] = "../a.py"
        case "invalid_commit":
            e["snapshot"]["commit"] = "main"
        case "missing_required":
            del graph["snapshot"]
        case "extra_nested":
            e["fault_probability"] = 1
        case "not_run_payload":
            stages["changes"]["status"] = "not_run"
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)


def test_indirect_and_rename_paths_use_correct_graph_revision() -> None:
    data = artifacts_report()
    impact = data["stages"]["impact"]["data"]
    impact["paths"][0]["nodes"] = ["c.py", "b.py", "a.py"]
    impact["candidates"][0].update(path="c.py", relationship="indirect")
    StageAnalysisReport.model_validate(data)
    # A renamed component points to its previous path in the base graph.
    c = data["stages"]["changes"]["data"]["components"][0]
    c.update(path="new.py", previous_path="a.py", change="renamed")
    data["stages"]["changes"]["data"]["files"][0]["path"] = "new.py"
    for name in ("graph", "impact"):
        data["stages"][name]["data"]["snapshot"] = data["identity"]["base"]
    StageAnalysisReport.model_validate(data)


@pytest.mark.parametrize("stage", ["inventory", "retrieval"])
def test_target_inventory_and_revision_bound_retrieval(stage: str) -> None:
    data = empty_report()
    snapshot = deepcopy(data["identity"]["target"])
    payload = (
        {"snapshot": snapshot, "framework": "pytest", "test_ids": [], "completeness": "complete"}
        if stage == "inventory"
        else {
            "sources": [
                {"snapshot": snapshot, "index_id": "index-1", "configuration_id": "lexical-v1"}
            ],
            "items": [
                {
                    "id": "chunk-1",
                    "snapshot": snapshot,
                    "index_id": "index-1",
                    "configuration_id": "lexical-v1",
                    "path": "a.py",
                    "rank": 1,
                    "location": {"line_start": 1, "line_end": 2},
                    "content_sha256": "3" * 64,
                }
            ],
        }
    )
    data["stages"][stage] = {"status": "completed", "data": payload}
    data["analysis_status"] = "partial"
    StageAnalysisReport.model_validate(data)
    snapshot["commit"] = "c" * 40
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)


@pytest.mark.parametrize(
    "native_ids",
    [
        [
            " tests/test_a.py::test_f[value] \t",
            "tests/test_a.py::test_f[ space inside ]",
            "tests/test_a.py::test_f[\u00e9]",
            "tests/test_a.py::test_f[e\u0301]",
            "tests/test_a.py::test_f[Case]",
            "tests/test_a.py::test_f[case]",
            "tests\\test_a.py::test_f[\\path::value]",
            "tests/test_a.py::test_f[" + "\u00e9" * 300 + "]",
        ],
        ["tests/test_a.py::test_f", "tests/test_a.py::test_f "],
        [" \t"],
    ],
)
def test_inventory_native_ids_survive_report_round_trip(native_ids: list[str]) -> None:
    data = empty_report()
    data["report_id"] = " example-report "  # Metadata Text keeps its existing policy.
    data["stages"]["inventory"] = {
        "status": "completed",
        "data": {
            "snapshot": data["identity"]["target"],
            "framework": "pytest",
            "test_ids": native_ids,
            "completeness": "complete",
        },
    }
    data["analysis_status"] = "partial"
    report = validate_report_json(json.dumps(data, ensure_ascii=False))
    assert isinstance(report, StageAnalysisReport)
    assert report.stages.inventory.data.test_ids == native_ids
    assert report.report_id == "example-report"
    restored = validate_report_json(report.model_dump_json())
    assert isinstance(restored, StageAnalysisReport)
    assert restored.stages.inventory.data.test_ids == native_ids


@pytest.mark.parametrize("native_id", ["", None, 1, True, b"tests/test_a.py::test_f", [], {}])
def test_inventory_native_ids_require_nonempty_strings(native_id: object) -> None:
    with pytest.raises(ValidationError):
        InventoryPayload.model_validate(
            {
                "snapshot": empty_report()["identity"]["target"],
                "framework": "pytest",
                "test_ids": [native_id],
                "completeness": "complete",
            }
        )


def test_legacy_native_id_trimming_is_unchanged(demo_data: dict) -> None:
    original = demo_data["selection"]["selected"][0]["test_id"]
    demo_data["selection"]["selected"][0]["test_id"] = f" {original}\t"
    report = validate_report_json(json.dumps(demo_data))
    assert report.schema_version == "1.0.0"
    assert report.selection.selected[0].test_id == original


@pytest.mark.parametrize("status", ["not_run", "not_implemented", "failed", "partial", "completed"])
def test_stage_state_matrix(status: str) -> None:
    data = empty_report()
    stage = {"status": status}
    if status in {"completed", "partial"}:
        stage["data"] = {"components": [], "files": []}
        if status == "partial":
            stage["limitations"] = [{"code": "bounded_scope"}]
        data["analysis_status"] = "partial"
    elif status == "failed":
        stage["error_code"] = "change_analysis_failed"
        data["analysis_status"] = "failed"
    else:
        stage["reason"] = "prerequisite_unavailable"
        data["analysis_status"] = status
    data["stages"]["changes"] = stage
    report = StageAnalysisReport.model_validate(data)
    assert report.stages.changes.status == status
    if status in {"not_run", "not_implemented"}:
        del stage["reason"]
    elif status == "failed":
        del stage["error_code"]
    elif status == "partial":
        del stage["limitations"]
    else:
        del stage["data"]
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)


def test_public_stage_models_export_without_new_routes() -> None:
    root = Path(__file__).resolve().parents[3]
    schema = json.loads((root / "contracts/generated/openapi.json").read_text("utf-8"))
    for name in ("StageAnalysisReport", "EvidenceBundle", "InventoryPayload", "RetrievalPayload"):
        assert name in schema["components"]["schemas"]
    assert set(schema["paths"]) == {"/health"}


def test_snapshot_failure_can_report_resolved_commits_without_invented_manifest_hashes() -> None:
    data = empty_report()
    data["identity"]["base"]["snapshot_id"] = None
    data["identity"]["target"]["snapshot_id"] = None
    data["analysis_status"] = "failed"
    data["stages"]["snapshots"] = {"status": "failed", "error_code": "snapshot_objects_missing"}
    report = StageAnalysisReport.model_validate(data)
    assert report.identity.base.snapshot_id is None
    # A graph cannot claim snapshot provenance when there is no manifest hash.
    data["stages"]["graph"] = {
        "status": "completed",
        "data": {
            "snapshot": data["identity"]["target"],
            "nodes": [],
            "edges": [],
            "unresolved": [],
        },
    }
    data["analysis_status"] = "partial"
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)


def test_direct_candidate_can_have_an_additional_indirect_supported_path() -> None:
    data = artifacts_report()
    data["stages"]["graph"]["data"]["edges"].extend(
        [
            {"source": "b.py", "target": "c.py", "kind": "absolute_import"},
            {"source": "c.py", "target": "a.py", "kind": "absolute_import"},
        ]
    )
    impact = data["stages"]["impact"]["data"]
    impact["paths"].append(
        {"id": "path-2", "changed_component_id": "changed", "nodes": ["b.py", "c.py", "a.py"]}
    )
    impact["candidates"][0]["path_ids"].append("path-2")
    StageAnalysisReport.model_validate(data)


def test_empty_retrieval_keeps_index_provenance_and_rejects_wrong_config() -> None:
    data = empty_report()
    source = {
        "snapshot": data["identity"]["target"],
        "index_id": "index-1",
        "configuration_id": "lexical-v1",
    }
    payload = {"sources": [source], "items": []}
    data["stages"]["retrieval"] = {"status": "completed", "data": payload}
    data["analysis_status"] = "partial"
    StageAnalysisReport.model_validate(data)
    payload["items"].append(
        {
            **source,
            "id": "chunk-1",
            "configuration_id": "other-config",
            "path": "a.py",
            "rank": 1,
            "content_sha256": "3" * 64,
            "location": {"line_start": 1, "line_end": 2},
        }
    )
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)


def test_run_identity_versions_and_unknowns_are_strict() -> None:
    data = empty_report()
    del data["schema_version"]
    with pytest.raises(ValidationError):
        validate_report_json(json.dumps(data))
    data = empty_report()
    data["identity"]["repository_id"] = "C:/private/repo"
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)


def test_partial_prerequisite_cannot_disappear_in_impact() -> None:
    data = artifacts_report()
    data["stages"]["graph"]["status"] = "partial"
    data["stages"]["graph"]["limitations"] = [{"code": "bounded_graph"}]
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)
    data["stages"]["impact"]["status"] = "partial"
    data["stages"]["impact"]["limitations"] = [{"code": "bounded_graph"}]
    StageAnalysisReport.model_validate(data)


def test_deleted_component_is_valid_in_base_graph_only() -> None:
    data = artifacts_report()
    component = data["stages"]["changes"]["data"]["components"][0]
    component.update(change="deleted", target_location=None)
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)
    for stage in ("graph", "impact"):
        data["stages"][stage]["data"]["snapshot"] = data["identity"]["base"]
    StageAnalysisReport.model_validate(data)


def test_duplicate_inventory_and_partial_inventory_are_not_complete() -> None:
    data = empty_report()
    inventory = {
        "snapshot": data["identity"]["target"],
        "framework": "pytest",
        "test_ids": ["tests/test_a.py::test_f"],
        "completeness": "partial",
    }
    data["stages"]["inventory"] = {"status": "completed", "data": inventory}
    data["analysis_status"] = "partial"
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)
    data["stages"]["inventory"].update(
        status="partial", limitations=[{"code": "discovery_partial"}]
    )
    StageAnalysisReport.model_validate(data)
    inventory["test_ids"] *= 2
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)


def test_evidence_verification_fields_are_explicit_producer_assertions() -> None:
    data = artifacts_report()
    for item in data["stages"]["evidence"]["data"]["items"]:
        item.update(
            resolution="resolved", support="supported", verification_reason="fixture_assertion"
        )
    data["stages"]["evidence"].update(status="completed", limitations=[])
    report = StageAnalysisReport.model_validate(data)
    assert report.stages.evidence.data.items[0].support == "supported"
    # No source verifier ran. The JSON validator checks consistency of assertions only.
    del data["stages"]["evidence"]["data"]["items"][0]["verification_reason"]
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)


def test_same_commit_cannot_have_two_different_known_snapshot_hashes() -> None:
    data = empty_report()
    data["identity"]["target"]["commit"] = data["identity"]["base"]["commit"]
    with pytest.raises(ValidationError):
        StageAnalysisReport.model_validate(data)
    data["identity"]["target"] = deepcopy(data["identity"]["base"])
    StageAnalysisReport.model_validate(data)

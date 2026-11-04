from dataclasses import replace

import pytest

from smartregression.contracts.stages import StageResult
from smartregression.core.selection.mapping import (
    CollectedTestSource,
    MappingValidationError,
    build_component_test_mapping,
)


def test_real_import_paths_link_exact_existing_ids_at_file_granularity(mapping_inputs):
    inputs = mapping_inputs()
    result = build_component_test_mapping(**inputs)
    assert result.status == "completed"
    assert {r.test_id: r.nodes for r in result.relationships} == {
        " test[đ] ": ("tests/test_direct.py", "logic.py"),
        "tests/test_indirect.py::test_y[param::with/slash]": (
            "tests/test_indirect.py",
            "helper.py",
            "logic.py",
        ),
    }
    assert all(r.changed_component_id == "changed-function" for r in result.relationships)
    assert all(r.granularity == "test_file_to_component_module" for r in result.relationships)
    assert result.provenance.inventory_digest
    assert result.provenance.rule_version == "pytest-import-file/1"
    assert result.safe_to_exclude is False


def test_node_id_text_is_never_used_to_infer_its_file(mapping_inputs):
    inputs = mapping_inputs([("logic.py::fake_hint", "tests/test_indirect.py")])
    result = build_component_test_mapping(**inputs)
    assert result.relationships[0].nodes == ("tests/test_indirect.py", "helper.py", "logic.py")


@pytest.mark.parametrize(
    "bindings,reason",
    [
        ([("opaque", None)], "test_source_unavailable"),
        ([("opaque", "not_present.py")], "test_source_not_in_snapshot"),
        ([("opaque", "tests/test_unrelated.py")], "no_supported_test_relationship"),
    ],
)
def test_unresolved_is_explicit_and_never_a_safe_exclusion(mapping_inputs, bindings, reason):
    result = build_component_test_mapping(**mapping_inputs(bindings))
    assert result.status == "partial"
    assert not result.relationships
    assert any(u.reason == reason and u.test_id == "opaque" for u in result.unresolved)
    assert result.safe_to_exclude is False


def test_missing_metadata_does_not_guess_from_standard_node_id(mapping_inputs):
    inputs = mapping_inputs([("tests/test_direct.py::test_x", "tests/test_direct.py")])
    inputs["test_sources"] = None
    result = build_component_test_mapping(**inputs)
    assert result.status == "partial" and not result.relationships
    assert any(u.reason == "test_source_unavailable" for u in result.unresolved)


@pytest.mark.parametrize(
    "change",
    [
        lambda i: i.update(configuration_digest="d" * 64),
        lambda i: i.update(inventory_id="other"),
        lambda i: i.update(identity=i["identity"].model_copy(update={"run_id": "other"})),
        lambda i: i.update(test_sources=replace(i["test_sources"], inventory_digest="0" * 64)),
    ],
)
def test_foreign_or_stale_source_receipt_rejects(mapping_inputs, change):
    inputs = mapping_inputs()
    change(inputs)
    with pytest.raises(MappingValidationError):
        build_component_test_mapping(**inputs)


def test_unknown_ids_and_duplicate_bindings_reject_instead_of_being_added(mapping_inputs):
    for sources in [
        (CollectedTestSource("unknown", "tests/test_direct.py"),),
        (CollectedTestSource(" test[đ] ", "tests/test_direct.py"),) * 2,
    ]:
        inputs = mapping_inputs()
        inputs["test_sources"] = replace(inputs["test_sources"], sources=sources)
        with pytest.raises(MappingValidationError):
            build_component_test_mapping(**inputs)


@pytest.mark.parametrize("status", ["failed", "not_run", "not_implemented"])
def test_inactive_inventory_cannot_be_successful_empty_mapping(mapping_inputs, status):
    inputs = mapping_inputs()
    inputs["inventory"] = StageResult(
        status=status,
        error_code="collection_failed" if status == "failed" else None,
        reason="collector_unavailable" if status != "failed" else None,
    )
    inputs["test_sources"] = None
    result = build_component_test_mapping(**inputs)
    assert result.status == ("failed" if status == "failed" else "not_run")
    assert not result.relationships


def test_partial_inventory_preserves_positive_relationships_and_limitations(mapping_inputs):
    inputs = mapping_inputs()
    data = inputs["inventory"].data.model_copy(update={"completeness": "partial"})
    inputs["inventory"] = StageResult(
        status="partial", data=data, limitations=[{"code": "collection_errors"}]
    )
    from smartregression.core.selection.mapping import inventory_digest

    inputs["test_sources"] = replace(
        inputs["test_sources"], inventory_digest=inventory_digest(inputs["inventory"])
    )
    result = build_component_test_mapping(**inputs)
    assert result.status == "partial" and result.relationships
    assert any(u.reason == "inventory_collection_errors" for u in result.unresolved)


@pytest.mark.parametrize("which", ["inventory", "graph", "impact"])
def test_base_or_foreign_target_data_is_rejected(mapping_inputs, which):
    inputs = mapping_inputs()
    inputs[which] = inputs[which].model_copy(
        update={"data": inputs[which].data.model_copy(update={"snapshot": inputs["identity"].base})}
    )
    with pytest.raises(MappingValidationError, match="mapping_requires_target_payloads"):
        build_component_test_mapping(**inputs)


def test_modified_test_file_maps_to_itself_without_inventing_function_usage(mapping_inputs):
    inputs = mapping_inputs([("opaque", "tests/test_direct.py")])
    from smartregression.contracts.stages import ChangePayload, FileCoverage, StageComponent
    from smartregression.core.impact.potential_impact import build_potential_impact

    inputs["changes"] = StageResult(
        status="completed",
        data=ChangePayload(
            components=[
                StageComponent(
                    id="test-change",
                    path="tests/test_direct.py",
                    kind="module",
                    change="modified",
                    reason="content_changed",
                )
            ],
            files=[FileCoverage(path="tests/test_direct.py", status="completed", limitations=[])],
        ),
    )
    inputs["impact"] = StageResult(
        status="completed",
        data=build_potential_impact(
            inputs["identity"], inputs["changes"].data, inputs["graph"].data
        ),
    )
    result = build_component_test_mapping(**inputs)
    assert len(result.relationships) == 1
    assert result.relationships[0].nodes == ("tests/test_direct.py",)
    assert result.relationships[0].relationship == "changed"
    assert result.relationships[0].impact_path_id is None


def test_deleted_component_retains_base_only_reason_and_never_maps_target_tests(mapping_inputs):
    inputs = mapping_inputs()
    from smartregression.contracts.stages import ChangePayload, FileCoverage, StageComponent
    from smartregression.core.impact.potential_impact import build_potential_impact

    inputs["changes"] = StageResult(
        status="completed",
        data=ChangePayload(
            components=[
                StageComponent(
                    id="deleted",
                    path="gone.py",
                    kind="module",
                    change="deleted",
                    reason="file_deleted",
                )
            ],
            files=[FileCoverage(path="gone.py", status="completed", limitations=[])],
        ),
    )
    inputs["impact"] = StageResult(
        status="completed",
        data=build_potential_impact(
            inputs["identity"], inputs["changes"].data, inputs["graph"].data
        ),
    )
    result = build_component_test_mapping(**inputs)
    assert not result.relationships
    assert any(
        u.changed_component_id == "deleted" and u.reason == "component_deleted_no_target"
        for u in result.unresolved
    )


def test_rename_uses_new_target_path_not_old_name(mapping_inputs):
    inputs = mapping_inputs()
    from smartregression.core.impact.potential_impact import build_potential_impact

    changes = inputs["changes"].data
    component = changes.components[0].model_copy(
        update={"change": "renamed", "previous_path": "old_logic.py"}
    )
    inputs["changes"] = StageResult(
        status="completed", data=changes.model_copy(update={"components": [component]})
    )
    inputs["impact"] = StageResult(
        status="completed",
        data=build_potential_impact(
            inputs["identity"], inputs["changes"].data, inputs["graph"].data
        ),
    )
    result = build_component_test_mapping(**inputs)
    assert all(r.nodes[-1] == "logic.py" for r in result.relationships)


def test_missing_or_unsupported_impact_path_cannot_create_a_relationship(mapping_inputs):
    inputs = mapping_inputs()
    data = inputs["impact"].data
    data.paths[0].nodes[:] = ["tests/test_direct.py", "helper.py", "logic.py"]
    with pytest.raises(MappingValidationError):
        build_component_test_mapping(**inputs)


def test_empty_complete_inventory_is_not_evidence_components_have_no_tests(mapping_inputs):
    result = build_component_test_mapping(**mapping_inputs([]))
    assert result.status == "partial" and not result.relationships
    assert any(u.reason == "component_has_no_supported_test" for u in result.unresolved)
    assert result.safe_to_exclude is False


def test_determinism_and_native_variants_are_never_deduplicated_by_label(mapping_inputs):
    bindings = [
        (" id ", "tests/test_direct.py"),
        ("id", "tests/test_direct.py"),
        ("é", "tests/test_indirect.py"),
        ("e\u0301", "tests/test_indirect.py"),
    ]
    inputs = mapping_inputs(bindings)
    result = build_component_test_mapping(**inputs)
    assert result == build_component_test_mapping(**inputs)
    assert [r.test_id for r in result.relationships] == [b[0] for b in bindings]


def test_output_bound_errors_without_truncating_relationships(mapping_inputs, monkeypatch):
    monkeypatch.setattr("smartregression.core.selection.mapping.MAX_RELATIONSHIPS", 1)
    with pytest.raises(MappingValidationError, match="mapping_relationship_limit"):
        build_component_test_mapping(**mapping_inputs())

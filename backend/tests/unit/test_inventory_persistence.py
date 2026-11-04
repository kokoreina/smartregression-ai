import json
from dataclasses import replace

import pytest

from smartregression.application.inventory_store import (
    InventoryConfiguration,
    InventoryMetadataError,
    UnsupportedTestId,
    prepare_inventory,
    require_complete_inventory_ids,
    validate_inventory_write,
)
from smartregression.application.inventory_store import (
    test_id_digest as native_digest,
)
from smartregression.contracts.stages import InventoryPayload, RunIdentity, StageResult


def configuration():
    return InventoryConfiguration(
        "candidate-inventory/1", "sqlparse", "sha256:" + "a" * 64, "b" * 64, "c" * 64, "d" * 64
    )


def inventory_write(data, ids=(" test[đ] ",), status="completed"):
    identity = RunIdentity.model_validate(data["identity"])
    active = status in {"completed", "partial"}
    stage = StageResult[InventoryPayload](
        status=status,
        data=InventoryPayload(
            snapshot=identity.target,
            framework="pytest",
            test_ids=list(ids),
            completeness="partial" if status == "partial" else "complete",
        )
        if active
        else None,
        reason="not_scheduled" if status in {"not_run", "not_implemented"} else None,
        error_code="collection_failed" if status == "failed" else None,
        limitations=[{"code": "collection_errors"}] if status == "partial" else [],
    )
    return prepare_inventory(
        identity=identity, inventory_id="inventory-1", stage=stage, configuration=configuration()
    )


@pytest.mark.parametrize("status", ["not_implemented", "not_run", "failed", "partial", "completed"])
@pytest.mark.parametrize("ids", [(), (" ", "test[é]", "test[e\u0301]", "x" * 9000)])
def test_freeze_and_roundtrip_states_exact_ids(stage_artifacts, status, ids):
    write = inventory_write(stage_artifacts, ids, status)
    assert validate_inventory_write(write) == write
    if write.stage.data:
        assert write.stage.data.test_ids == list(ids)
        assert json.loads(write.stage_json)["data"]["test_ids"] == list(ids)
    assert native_digest("test") != native_digest("test ")


@pytest.mark.parametrize("value", ["test\0id", "test\ud800"])
def test_unsupported_postgresql_text_is_explicit(stage_artifacts, value):
    with pytest.raises((UnsupportedTestId, ValueError)):
        inventory_write(stage_artifacts, (value,))
    with pytest.raises(UnsupportedTestId, match="unsupported_test_id"):
        native_digest(value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("configuration_sha256", "e" * 64),
        ("configuration_json", "{}"),
        ("stage_json", "{}"),
        ("inventory_id", " bad "),
        ("duration_seconds", float("nan")),
        ("exit_code", True),
        ("diagnostic_artifact_id", "x\0y"),
    ],
)
def test_mutated_frozen_input_is_revalidated(stage_artifacts, field, value):
    with pytest.raises(InventoryMetadataError):
        validate_inventory_write(replace(inventory_write(stage_artifacts), **{field: value}))


def test_partial_and_completeness_must_agree(stage_artifacts):
    write = inventory_write(stage_artifacts, status="partial")
    data = json.loads(write.stage_json)
    data["data"]["completeness"] = "complete"
    from smartregression.core.git.snapshots import canonical_json

    with pytest.raises(InventoryMetadataError):
        validate_inventory_write(replace(write, stage_json=canonical_json(data).decode()))


@pytest.mark.parametrize("status", ["not_implemented", "not_run", "failed", "partial"])
def test_incomplete_inventory_is_never_eligible_for_dispatch(stage_artifacts, status):
    write = inventory_write(stage_artifacts, (), status)
    with pytest.raises(InventoryMetadataError):
        require_complete_inventory_ids(
            write, identity=write.identity, configuration_sha256=write.configuration_sha256
        )

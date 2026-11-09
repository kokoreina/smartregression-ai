"""Application metadata preparation, not database persistence acceptance."""

import hashlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from smartregression.application.run_store import (
    ReportArtifact,
    RunConfiguration,
    RunMetadataError,
    prepare_run_report,
    validate_run_report_write,
)
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.git.snapshots import SnapshotLimits, SnapshotManifest, canonical_json


def inputs(data):
    report = StageAnalysisReport.model_validate(data)
    raw = report.model_dump_json(indent=2).encode() + b"\n"
    artifact = ReportArtifact(
        "artifact-1", "reports/run/report.json", hashlib.sha256(raw).hexdigest(), len(raw)
    )
    manifests = tuple(
        SnapshotManifest(
            s.repository_id, s.commit, (), s.snapshot_id, "snapshot/actual", "materializer/actual"
        )
        for s in (report.identity.base, report.identity.target)
        if s.snapshot_id is not None
    )
    config = RunConfiguration("0.1.0", SnapshotLimits(), 256000, (("graph", None),))
    return dict(
        report=report,
        configuration=config,
        snapshot_manifests=manifests,
        artifact=artifact,
        published_report_bytes=raw,
    )


def test_metadata_preserves_identity_status_null_metrics_and_actual_versions(stage_artifacts):
    args = inputs(stage_artifacts)
    result = prepare_run_report(**args)
    assert result.identity == args["report"].identity
    assert result.analysis_status == "partial"
    assert result.analysis_duration_seconds == args["report"].analysis_duration_seconds
    assert result.llm_cost_usd is None
    assert result.snapshots[0].manifest_version == "snapshot/actual"
    assert result.snapshots[0].materializer_version == "materializer/actual"
    assert result.configuration_sha256 == hashlib.sha256(result.configuration_json).hexdigest()
    summary = json.loads(result.stage_summary_json)
    assert set(summary) == set(type(args["report"].stages).model_fields)
    assert all("data" not in value for value in summary.values())
    assert b"excerpt" not in result.stage_summary_json
    with pytest.raises(FrozenInstanceError):
        result.report_id = "changed"


@pytest.mark.parametrize(
    "name", ["inventory_configuration_digest", "retrieval_configuration_digest"]
)
def test_optional_collector_digest_roundtrips_without_changing_absent_config(stage_artifacts, name):
    args = inputs(stage_artifacts)
    assert name not in json.loads(args["configuration"].canonical_bytes())
    args["configuration"] = replace(args["configuration"], **{name: "c" * 64})
    write = prepare_run_report(**args)
    assert validate_run_report_write(write) == write
    assert json.loads(write.configuration_json)[name] == "c" * 64
    with pytest.raises(RunMetadataError):
        replace(args["configuration"], **{name: "bad"}).canonical_bytes()


def test_configuration_is_explicit_bounded_and_not_arbitrary_secret_dictionary():
    first = RunConfiguration(None, SnapshotLimits(), 256000, (("graph", None),))
    assert json.loads(first.canonical_bytes())["application_version"] is None
    assert first.canonical_bytes() == first.canonical_bytes()
    for versions in (
        (("database_url", "secret"),),
        (("graph", "postgresql://secret"),),
        (("graph", "1"), ("graph", "2")),
    ):
        with pytest.raises(RunMetadataError):
            RunConfiguration(None, SnapshotLimits(), 256000, versions).canonical_bytes()
    with pytest.raises(TypeError):
        RunConfiguration(database_url="secret")


def test_manifest_missing_foreign_or_inconsistent_is_rejected(stage_artifacts):
    args = inputs(stage_artifacts)
    with pytest.raises(RunMetadataError):
        prepare_run_report(**(args | {"snapshot_manifests": ()}))
    manifests = args["snapshot_manifests"]
    for changed in (
        replace(manifests[0], repository_id="foreign"),
        replace(manifests[0], schema_version=""),
    ):
        with pytest.raises(RunMetadataError):
            prepare_run_report(**(args | {"snapshot_manifests": (changed, *manifests[1:])}))


def test_published_bytes_digest_and_report_cannot_disagree(stage_artifacts):
    args = inputs(stage_artifacts)
    raw = args["published_report_bytes"]
    for altered in (raw + b" ", b"not-json", canonical_json({})):
        with pytest.raises(RunMetadataError):
            prepare_run_report(**(args | {"published_report_bytes": altered}))
    other = args["report"].model_copy(update={"report_id": "other"})
    with pytest.raises(RunMetadataError):
        prepare_run_report(**(args | {"report": other}))


@pytest.mark.parametrize("identifier", ["bad\0id", "é" * 257])
def test_persistence_id_limits_do_not_change_public_contract(stage_artifacts, identifier):
    args = inputs(stage_artifacts)
    # Canonical report accepts this Text; persistence explicitly rejects it.
    data = args["report"].model_dump(mode="json")
    data["report_id"] = identifier
    StageAnalysisReport.model_validate(data)
    matching = inputs(data)
    with pytest.raises(RunMetadataError):
        prepare_run_report(**matching)
    with pytest.raises(RunMetadataError):
        replace(args["artifact"], artifact_id=identifier)


def test_unicode_id_byte_boundary_and_run_id_limits(stage_artifacts):
    data = json.loads(json.dumps(stage_artifacts))
    data["report_id"] = "é" * 256
    assert prepare_run_report(**inputs(data)).report_id == "é" * 256
    data["identity"]["run_id"] = "é" * 257
    with pytest.raises(RunMetadataError):
        prepare_run_report(**inputs(data))


def test_configuration_order_is_canonical_and_invalid_limits_are_rejected():
    first = RunConfiguration(
        "0.1.0", SnapshotLimits(), 256000, (("snapshots", "snapshot/1"), ("graph", None))
    )
    second = replace(first, producer_versions=tuple(reversed(first.producer_versions)))
    assert first.canonical_bytes() == second.canonical_bytes()
    for changed in (
        {"python_source_limit_bytes": 0},
        {"python_source_limit_bytes": True},
        {"graph_policy": "base_imports"},
    ):
        with pytest.raises(RunMetadataError):
            replace(first, **changed).canonical_bytes()


def test_report_summary_size_is_bounded_without_dropping_limitations(stage_artifacts):
    data = json.loads(json.dumps(stage_artifacts))
    data["stages"]["evidence"]["limitations"] = [{"code": "x" * 270000}]
    with pytest.raises(RunMetadataError):
        prepare_run_report(**inputs(data))


def test_duplicate_snapshots_are_deduplicated_but_versions_cannot_conflict(stage_artifacts):
    args = inputs(stage_artifacts)
    manifests = args["snapshot_manifests"]
    duplicate = (*manifests, manifests[0])
    assert len(prepare_run_report(**(args | {"snapshot_manifests": duplicate})).snapshots) == 2
    conflicting = (*manifests, replace(manifests[0], materializer_version="different/1"))
    with pytest.raises(RunMetadataError):
        prepare_run_report(**(args | {"snapshot_manifests": conflicting}))


def test_storage_error_codes_are_stable():
    from smartregression.application.run_store import RunConflict, RunStorageError

    assert str(RunConflict()) == "run_storage_conflict"
    assert isinstance(RunConflict(), RunStorageError)
    assert str(RunStorageError()) == "run_storage_failed"


def test_invalid_python_input_shapes_fail_with_safe_code(stage_artifacts):
    args = inputs(stage_artifacts)
    for changes in (
        {"configuration": {"password": "secret"}},
        {"report": {}},
        {"snapshot_manifests": (None,)},
        {"published_report_bytes": None},
    ):
        with pytest.raises(RunMetadataError, match="run_metadata_invalid"):
            prepare_run_report(**(args | changes))
    for changes in ({"storage_key": 123}, {"size_bytes": 2**63}):
        with pytest.raises(RunMetadataError):
            replace(args["artifact"], **changes)


@pytest.mark.parametrize(
    "key",
    [
        "../report.json",
        "/report.json",
        "C:/report.json",
        "reports\\report.json",
        "https://host/report",
        "a//b",
    ],
)
def test_artifact_storage_key_is_only_a_backend_relative_locator(key):
    with pytest.raises(RunMetadataError):
        ReportArtifact("artifact-1", key, "a" * 64, 10)


def test_failure_identity_does_not_require_invented_snapshot_rows(stage_artifacts):
    data = stage_artifacts.copy()
    data["identity"] = json.loads(json.dumps(data["identity"]))
    data["identity"]["base"]["snapshot_id"] = None
    data["identity"]["target"]["snapshot_id"] = None
    data["analysis_status"] = "failed"
    data["stages"] = {
        name: {"status": "failed", "error_code": "producer_failed"} for name in data["stages"]
    }
    args = inputs(data)
    result = prepare_run_report(**args)
    assert result.snapshots == ()
    assert result.analysis_status == "failed"
    assert result.identity.base.snapshot_id is None


def test_mutated_nested_report_is_revalidated_before_boundary(stage_artifacts):
    args = inputs(stage_artifacts)
    args["report"].stages.impact.data.candidates[0].evidence_ids.append("unknown")
    with pytest.raises(RunMetadataError):
        prepare_run_report(**args)

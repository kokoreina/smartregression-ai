"""Actual workflow/mapping with an explicitly injected collection-receipt double."""

import json
from dataclasses import asdict

import pytest
from test_analysis_workflow import BASE, TARGET, Source

from smartregression.application.analysis import AnalysisError, analyze_execution
from smartregression.application.inventory_store import InventoryConfiguration
from smartregression.application.mapping_artifact import verify_mapping_artifact
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.core.execution.inventory import finalize_discovery

TEST_ID = "tests/test_a.py::test_value[ é ]"


class Collector:
    configuration = InventoryConfiguration(
        "candidate-inventory/2",
        "owned-workflow",
        "sha256:" + "a" * 64,
        "b" * 64,
        "c" * 64,
        "d" * 64,
    )

    def __init__(self, *, corrupt=None, failed=False, partial=False):
        self.last_observation = {}
        self.corrupt, self.failed = corrupt, failed
        self.partial = partial
        self.calls = 0

    @property
    def configuration_digest(self):
        return self.configuration.digest

    def collect(self, snapshot, *, identity):
        self.calls += 1
        payload = dict(
            ids=[] if self.failed else [TEST_ID],
            exit_code=2 if self.failed or self.partial else 0,
            collection_finished=True,
            collection_errors=1 if self.failed else 0,
        )
        self.last_observation = dict(
            configuration_sha256=self.configuration.digest,
            configuration=json.loads(self.configuration.canonical_bytes()),
            result=dict(
                protocol="inventory/2",
                mode="collect",
                identity=asdict(identity),
                collection=payload,
                test_sources=dict(
                    version="pytest-item-path/1",
                    items=[dict(test_id=TEST_ID, path="tests/test_a.py")],
                ),
            ),
        )
        if self.corrupt == "identity":
            self.last_observation["result"]["identity"]["run_id"] = "other-run"
        if self.corrupt == "test_id":
            self.last_observation["result"]["test_sources"]["items"][0]["test_id"] = "unknown"
        if self.corrupt == "configuration":
            self.last_observation["configuration_sha256"] = "f" * 64
        return finalize_discovery(expected=identity, observed=identity, payload=payload)


def execute(tmp_path, collector):
    before = {
        "a.py": b"def f():\n    return 1\n",
        "tests/test_a.py": b"import a\ndef test_value():\n    assert a.f()\n",
    }
    source = Source(tmp_path, before, before | {"a.py": b"def f():\n    return 2\n"})
    return analyze_execution(
        source,
        authorization=RepositoryAuthorization("fixture", tmp_path),
        repository_id="fixture",
        base=BASE,
        target=TARGET,
        data_kind="demo",
        mapping_collector=collector,
    )


def test_workflow_maps_actual_impact_and_binds_sidecar_to_report(tmp_path):
    collector = Collector()
    execution = execute(tmp_path, collector)
    sidecar = execution.mapping_artifact
    assert collector.calls == 1
    document = json.loads(sidecar.raw)
    assert document["schema_version"] == "report-mapping/1"
    assert document["report_id"] == execution.report.report_id
    assert document["identity"] == execution.report.identity.model_dump(mode="json")
    assert document["mapping"]["safe_to_exclude"] is False
    assert {r["test_id"] for r in document["mapping"]["relationships"]} == {TEST_ID}
    assert (
        verify_mapping_artifact(sidecar.raw, expected=sidecar, report=execution.report) == document
    )
    with pytest.raises(ValueError, match="mapping_artifact_mismatch"):
        verify_mapping_artifact(sidecar.raw + b" ", expected=sidecar, report=execution.report)
    other = execution.report.model_copy(update={"report_id": "other-report"})
    with pytest.raises(ValueError, match="mapping_artifact_mismatch"):
        verify_mapping_artifact(sidecar.raw, expected=sidecar, report=other)


@pytest.mark.parametrize("corrupt", ["identity", "test_id", "configuration"])
def test_forged_receipt_cannot_create_successful_mapping(tmp_path, corrupt):
    with pytest.raises(AnalysisError, match="mapping_validation_failed"):
        execute(tmp_path, Collector(corrupt=corrupt))


def test_failed_inventory_produces_failed_mapping_not_successful_empty(tmp_path):
    execution = execute(tmp_path, Collector(failed=True))
    document = json.loads(execution.mapping_artifact.raw)
    assert execution.report.stages.inventory.status == "failed"
    assert document["mapping"]["status"] == "failed"
    assert document["mapping"]["relationships"] == []
    assert document["mapping"]["unresolved"]


def test_partial_inventory_keeps_mapping_partial_and_native_ids(tmp_path):
    execution = execute(tmp_path, Collector(partial=True))
    document = json.loads(execution.mapping_artifact.raw)
    assert execution.report.stages.inventory.status == "partial"
    assert document["mapping"]["status"] == "partial"
    assert {r["test_id"] for r in document["mapping"]["relationships"]} == {TEST_ID}


def test_oversized_sidecar_fails_explicitly_without_truncation(tmp_path, monkeypatch):
    monkeypatch.setattr("smartregression.application.mapping_artifact.MAX_MAPPING_BYTES", 1)
    with pytest.raises(AnalysisError, match="mapping_validation_failed"):
        execute(tmp_path, Collector())

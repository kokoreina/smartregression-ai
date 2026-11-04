from dataclasses import replace

import pytest

from smartregression.application.inventory import collect_inventory, inventory_identity
from smartregression.application.stage_conversion import identity_from_snapshots
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.execution.inventory import finalize_discovery
from smartregression.core.git.snapshots import SnapshotPair, freeze_snapshot


def context():
    base = freeze_snapshot("fixture", "a" * 40, (), ())
    target = freeze_snapshot("fixture", "b" * 40, (), ())
    return target, identity_from_snapshots(SnapshotPair(base, target, "private"), run_id="run-1")


class Collector:
    configuration_digest = "c" * 64

    def __init__(self, ids=(), code=5, errors=0, termination="exited"):
        self.ids, self.code, self.errors, self.termination = ids, code, errors, termination
        self.calls = 0

    def collect(self, snapshot, *, identity):
        self.calls += 1
        return finalize_discovery(
            expected=identity,
            observed=identity,
            payload={
                "ids": list(self.ids),
                "exit_code": self.code,
                "collection_finished": True,
                "collection_errors": self.errors,
            },
            termination=self.termination,
        )


@pytest.mark.parametrize(
    "ids,code,errors,termination,status,completeness,error",
    [
        (["tests/test_a.py::test_one"], 0, 0, "exited", "completed", "complete", None),
        ([], 5, 0, "exited", "completed", "complete", None),
        (["test_one"], 2, 1, "exited", "partial", "partial", None),
        ([], 2, 1, "exited", "failed", None, "collection_failed"),
        ([], 5, 0, "timeout", "failed", None, "discovery_timeout"),
        ([], 5, 0, "output_limit", "failed", None, "output_limit"),
    ],
)
def test_discovery_maps_to_canonical_v2(
    ids, code, errors, termination, status, completeness, error
):
    target, identity = context()
    result = collect_inventory(target, identity, Collector(ids, code, errors, termination))
    assert result.status == status
    assert result.error_code == error
    if completeness:
        assert result.data.completeness == completeness
        assert result.data.test_ids == ids
        assert result.data.snapshot == identity.target
    else:
        assert result.data is None
    assert bool(result.limitations) == (status == "partial")


def test_wrong_snapshot_rejected_before_collector_call():
    target, identity = context()
    collector = Collector()
    other = freeze_snapshot("other", target.manifest.commit, (), ())
    result = collect_inventory(other, identity, collector)
    assert result.error_code == "inventory_identity_mismatch"
    assert collector.calls == 0


def test_stale_collector_result_rejected():
    target, identity = context()
    collector = Collector(["test_one"], 0)
    original = collector.collect
    collector.collect = lambda snapshot, *, identity: replace(
        original(snapshot, identity=identity),
        identity=replace(identity, run_id="old-run"),
    )
    assert (
        collect_inventory(target, identity, collector).error_code == "inventory_identity_mismatch"
    )


def test_forged_completed_result_cannot_hide_collection_error():
    target, identity = context()
    collector = Collector(["test_one"], 2, 1)
    original = collector.collect
    collector.collect = lambda snapshot, *, identity: replace(
        original(snapshot, identity=identity), status="complete", reason=None
    )
    assert collect_inventory(target, identity, collector).error_code == "invalid_discovery_result"


def test_native_ids_are_not_silently_trimmed_by_canonical_text():
    target, identity = context()
    result = collect_inventory(target, identity, Collector([" test_one "], 0))
    assert result.status == "completed"
    assert result.data.test_ids == [" test_one "]


def test_untrusted_exception_is_not_echoed():
    target, identity = context()

    class Broken(Collector):
        def collect(self, snapshot, *, identity):
            raise ValueError("private-token-and-source")

    result = collect_inventory(target, identity, Broken())
    assert result.error_code == "inventory_discovery_failed"
    assert "private" not in result.model_dump_json()


def test_inventory_fits_real_report_and_partial_is_not_lost(stage_artifacts):
    report = StageAnalysisReport.model_validate(stage_artifacts)
    from smartregression.application.inventory import inventory_stage

    expected = inventory_identity(report.identity, "c" * 64)
    result = finalize_discovery(
        expected=expected,
        observed=expected,
        payload={
            "ids": ["test_one"],
            "exit_code": 2,
            "collection_finished": True,
            "collection_errors": 1,
        },
    )
    stage_artifacts["stages"]["inventory"] = inventory_stage(result, report.identity).model_dump()
    validated = StageAnalysisReport.model_validate(stage_artifacts)
    assert validated.stages.inventory.status == "partial"
    assert validated.stages.inventory.data.completeness == "partial"

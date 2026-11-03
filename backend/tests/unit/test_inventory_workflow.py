import pytest
from test_analysis_workflow import Source, run

from smartregression.application.analysis import analysis_exit_code
from smartregression.application.inventory import collect_inventory
from smartregression.application.stage_conversion import identity_from_snapshots
from smartregression.core.execution.inventory import finalize_discovery
from smartregression.core.git.snapshots import SnapshotPair, freeze_snapshot


class Collector:
    configuration_digest = "c" * 64

    def __init__(self, code=0, errors=0, ids=None, termination="exited"):
        self.code, self.errors, self.ids, self.termination = code, errors, ids, termination
        self.calls = []

    def collect(self, snapshot, *, identity):
        self.calls.append((snapshot, identity))
        return finalize_discovery(
            expected=identity,
            observed=identity,
            payload={
                "ids": self.ids if self.ids is not None else ["tests/test_a.py::test_a"],
                "exit_code": self.code,
                "collection_finished": True,
                "collection_errors": self.errors,
            },
            termination=self.termination,
        )


@pytest.mark.parametrize("partial", [False, True])
def test_injected_collector_receives_exact_frozen_target_and_retains_completeness(
    tmp_path, partial
):
    collector = Collector(code=2 if partial else 0, errors=1 if partial else 0)
    report = run(Source(tmp_path), inventory_collector=collector)
    assert report.stages.inventory.status == ("partial" if partial else "completed")
    assert report.stages.inventory.data.snapshot == report.identity.target
    assert report.stages.inventory.data.completeness == ("partial" if partial else "complete")
    snapshot, invocation = collector.calls[0]
    assert invocation.run_id == report.identity.run_id
    assert invocation.snapshot_digest == snapshot.manifest.snapshot_id
    assert invocation.target_commit == report.identity.target.commit
    assert report.analysis_status == "partial"
    assert analysis_exit_code(report) == 1


def test_discovery_failure_survives_aggregate_partial_report(tmp_path):
    report = run(Source(tmp_path), inventory_collector=Collector(termination="timeout"))
    assert report.stages.snapshots.status == "completed"
    assert report.stages.inventory.status == "failed"
    assert report.stages.inventory.error_code == "discovery_timeout"
    assert report.stages.inventory.data is None
    assert report.analysis_status == "partial"
    assert analysis_exit_code(report) == 2


def test_successful_empty_inventory_is_distinct_from_failure(tmp_path):
    report = run(Source(tmp_path), inventory_collector=Collector(code=5, ids=[]))
    assert report.stages.inventory.status == "completed"
    assert report.stages.inventory.data.test_ids == []
    assert report.stages.inventory.data.completeness == "complete"


def test_configuration_digest_is_bound_and_bad_configuration_does_not_collect():
    snap = freeze_snapshot("fixture", "a" * 40, (), ())
    identity = identity_from_snapshots(SnapshotPair(snap, snap, "private"), run_id="run-1")
    collector = Collector()
    collector.configuration_digest = "invalid"
    assert collect_inventory(snap, identity, collector).status == "failed"
    assert collector.calls == []

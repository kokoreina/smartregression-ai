from dataclasses import replace
from types import SimpleNamespace

import pytest

from smartregression.adapters.runners.inventory_collector import FixtureInventoryCollector
from smartregression.adapters.runners.inventory_fixtures import fixture_sources
from smartregression.application.inventory import inventory_identity
from smartregression.application.stage_conversion import identity_from_snapshots
from smartregression.core.git.snapshots import SnapshotPair, TreeEntry, freeze_snapshot


def snapshot(sources):
    import hashlib

    entries, contents = [], []
    for path, content in sorted(sources.items()):
        blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        entries.append(TreeEntry(path, "100644", blob, len(content)))
        contents.append(content)
    return freeze_snapshot("fixture", "a" * 40, tuple(entries), tuple(contents))


def collector(root, worker):
    return FixtureInventoryCollector(worker, root)


class Worker:
    image = "sha256:" + "d" * 64
    limits = SimpleNamespace(timeout=2, memory_mib=256, cpus=1, pids=64, output_bytes=65536)

    def __init__(self, root):
        self.worker, self.seccomp = root / "worker.py", root / "seccomp.json"
        self.worker.write_bytes(b"trusted worker fixture")
        self.seccomp.write_bytes(b"{}")
        self.calls = []

    def run(self, root, digest):
        self.calls.append(root)
        assert (root / "tests/test_inventory.py").read_bytes() == fixture_sources("success")[
            "tests/test_inventory.py"
        ]
        return {
            "ids": ["tests/test_inventory.py::test_one"],
            "exit_code": 0,
            "collection_finished": True,
            "collection_errors": 0,
            "snapshot_digest": digest,
            "reports": [],
            "isolation": {
                "uid": 65534,
                "seccomp": 2,
                "no_new_privileges": True,
                "network": ["lo"],
                "memory_max": str(256 * 1024 * 1024),
                "pids_max": "64",
                "cpu_max": "100000 100000",
            },
        }


def collect(c, snap):
    run = identity_from_snapshots(SnapshotPair(snap, snap, "fixture"), run_id="run-1")
    return c.collect(snap, identity=inventory_identity(run, c.configuration_digest))


def test_authorized_fixture_materialized_as_data_and_collected(tmp_path):
    worker = Worker(tmp_path)
    c = collector(tmp_path, worker)
    result = collect(c, snapshot(fixture_sources("success")))
    assert result.status == "complete"
    assert result.identity.configuration_digest == c.configuration_digest
    assert len(worker.calls) == 1
    assert not worker.calls[0].exists()


def test_arbitrary_source_is_rejected_before_execution(tmp_path):
    worker = Worker(tmp_path)
    c = collector(tmp_path, worker)
    with pytest.raises(ValueError, match="fixture_not_authorized"):
        collect(c, snapshot({"tests/test_inventory.py": b"raise RuntimeError('untrusted')"}))
    assert worker.calls == []


def test_configuration_change_is_rejected_before_execution(tmp_path):
    worker = Worker(tmp_path)
    c = collector(tmp_path, worker)
    worker.worker.write_bytes(b"changed")
    with pytest.raises(ValueError, match="collector_configuration_changed"):
        collect(c, snapshot(fixture_sources("success")))
    assert worker.calls == []


def test_tampered_snapshot_is_rejected_before_execution(tmp_path):
    worker = Worker(tmp_path)
    c = collector(tmp_path, worker)
    snap = snapshot(fixture_sources("success"))
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        collect(c, replace(snap, contents=(b"changed",)))
    assert worker.calls == []

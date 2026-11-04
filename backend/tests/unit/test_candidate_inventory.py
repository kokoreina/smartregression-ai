import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from smartregression.adapters.runners.candidate_inventory import (
    CANDIDATES,
    CandidateInventoryCollector,
    decode_result,
    git_tree_digest,
)
from smartregression.core.execution.inventory import InventoryIdentity
from smartregression.core.git.snapshots import TreeEntry, freeze_snapshot


def identity():
    return InventoryIdentity("sqlparse", "run-1", "a" * 40, "b" * 64, "c" * 64)


def result():
    return dict(
        protocol="inventory/2",
        identity=asdict(identity()),
        mode="collect",
        test_sources={"version": "pytest-item-path/1", "items": []},
        collection=dict(ids=[], exit_code=5, collection_finished=True, collection_errors=0),
        isolation=dict(
            uid=65534,
            seccomp=2,
            no_new_privileges=True,
            network=["lo"],
            memory_max="536870912",
            pids_max="64",
            cpu_max="100000 100000",
        ),
        environment={},
        exclusions=dict(configuration={}, collection_skips=[]),
        duration_seconds=1,
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(protocol="other"),
        lambda r: r.update(identity={}),
        lambda r: r["isolation"].update(network=["lo", "eth0"]),
        lambda r: r["isolation"].update(cpu_max="max 100000"),
        lambda r: r["isolation"].update(memory_max="max"),
        lambda r: r.update(duration_seconds=float("nan")),
        lambda r: r.update(exclusions=[]),
        lambda r: r.update(protocol="inventory/1"),
        lambda r: r["test_sources"].update(items=[{"test_id": "unknown", "path": "test.py"}]),
        lambda r: r["test_sources"].update(version="other"),
    ],
)
def test_invalid_frame_scope_or_isolation_is_not_inventory(mutation):
    value = result()
    mutation(value)
    with pytest.raises(ValueError):
        decode_result(
            b"SMARTREGRESSION_INVENTORY=" + json.dumps(value).encode(), identity(), "collect"
        )


def test_duplicate_missing_or_malformed_frame_is_rejected():
    frame = b"SMARTREGRESSION_INVENTORY=" + json.dumps(result()).encode()
    assert decode_result(frame, identity(), "collect")["collection"]["ids"] == []
    for raw in [
        b"",
        frame + b"\n" + frame,
        b"SMARTREGRESSION_INVENTORY={",
        b'SMARTREGRESSION_INVENTORY={"a":1,"a":2}',
    ]:
        with pytest.raises(ValueError):
            decode_result(raw, identity(), "collect")


def test_snapshot_tree_matches_git_object_format_not_claimed_sha():
    raw = b"owned fixture\n"
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    snapshot = freeze_snapshot(
        "owned", "a" * 40, (TreeEntry("test.py", "100644", blob, len(raw)),), (raw,)
    )
    tree = b"100644 test.py\0" + bytes.fromhex(blob)
    assert (
        git_tree_digest(snapshot)
        == hashlib.sha1(b"tree " + str(len(tree)).encode() + b"\0" + tree).hexdigest()
    )


def test_accepted_revision_with_wrong_tree_cannot_reach_docker(monkeypatch):
    root = Path(__file__).resolve().parents[3]
    collector = CandidateInventoryCollector("sqlparse", "sha256:" + "a" * 64, root, root)
    snapshot = freeze_snapshot("sqlparse", CANDIDATES["sqlparse"][1], (), ())
    expected = InventoryIdentity(
        "sqlparse",
        "run-1",
        snapshot.manifest.commit,
        snapshot.manifest.snapshot_id,
        collector.configuration_digest,
    )
    calls = []
    monkeypatch.setattr(
        "smartregression.adapters.runners.candidate_inventory.bounded_command",
        lambda *a, **k: calls.append(a),
    )
    with pytest.raises(ValueError, match="candidate_not_authorized"):
        collector.collect(snapshot, identity=expected)
    assert calls == []

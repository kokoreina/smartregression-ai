"""Task-owned data; real static producers, explicit collection-metadata fixtures."""

import hashlib

from smartregression.application.stage_conversion import graph_result, identity_from_snapshots
from smartregression.contracts.stages import (
    ChangePayload,
    FileCoverage,
    InventoryPayload,
    StageComponent,
    StageResult,
)
from smartregression.core.execution.inventory import InventoryIdentity
from smartregression.core.git.snapshots import SnapshotPair, TreeEntry, freeze_snapshot
from smartregression.core.impact.dependency_graph import build_dependency_graph
from smartregression.core.impact.potential_impact import build_potential_impact
from smartregression.core.selection.mapping import (
    CollectedTestSource,
    MappingSources,
    inventory_digest,
)


def frozen(sources, commit="b" * 40, repository="mapping-fixture"):
    entries, contents = [], []
    for path, source in sorted(sources.items()):
        raw = source.encode()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        entries.append(TreeEntry(path, "100644", blob, len(raw)))
        contents.append(raw)
    return freeze_snapshot(repository, commit, tuple(entries), tuple(contents))


def mapping_inputs(bindings=None):
    sources = {
        "logic.py": "def compute():\n    return 2\n",
        "helper.py": "import logic\n",
        "tests/test_direct.py": (
            "import logic\ndef test_x():\n    raise RuntimeError('must_not_execute')\n"
        ),
        "tests/test_indirect.py": (
            "import helper\ndef test_y():\n    raise RuntimeError('must_not_execute')\n"
        ),
        "tests/test_unrelated.py": "def test_z():\n    raise RuntimeError('must_not_execute')\n",
    }
    target = frozen(sources)
    base = frozen(sources | {"logic.py": "def compute():\n    return 1\n"}, "a" * 40)
    identity = identity_from_snapshots(SnapshotPair(base, target, "owned-data"), run_id="run-1")
    changes = StageResult[ChangePayload](
        status="completed",
        data=ChangePayload(
            components=[
                StageComponent(
                    id="changed-function",
                    path="logic.py",
                    kind="function",
                    symbol="compute",
                    change="modified",
                    base_location={"line_start": 1, "line_end": 2},
                    target_location={"line_start": 1, "line_end": 2},
                    reason="content_changed",
                )
            ],
            files=[FileCoverage(path="logic.py", status="completed", limitations=[])],
        ),
    )
    graph = graph_result(
        build_dependency_graph(
            repository=identity.repository_id, revision=identity.target.commit, sources=sources
        ),
        identity.target,
    )
    impact = StageResult(
        status="completed", data=build_potential_impact(identity, changes.data, graph.data)
    )
    bindings = (
        bindings
        if bindings is not None
        else [
            (" test[đ] ", "tests/test_direct.py"),
            ("tests/test_indirect.py::test_y[param::with/slash]", "tests/test_indirect.py"),
        ]
    )
    inventory = StageResult[InventoryPayload](
        status="completed",
        data=InventoryPayload(
            snapshot=identity.target,
            framework="pytest",
            completeness="complete",
            test_ids=[item[0] for item in bindings],
        ),
    )
    manifest = MappingSources(
        identity=InventoryIdentity(
            identity.repository_id,
            identity.run_id,
            identity.target.commit,
            identity.target.snapshot_id,
            "c" * 64,
        ),
        inventory_id="inventory-1",
        inventory_digest=inventory_digest(inventory),
        sources=tuple(CollectedTestSource(*item) for item in bindings),
    )
    return dict(
        identity=identity,
        snapshot=target,
        inventory_id="inventory-1",
        configuration_digest="c" * 64,
        changes=changes,
        graph=graph,
        impact=impact,
        inventory=inventory,
        test_sources=manifest,
    )

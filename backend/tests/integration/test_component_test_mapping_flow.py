"""Real Git -> diff -> static graph/impact -> mapping. Collection receipt is a fixture.

No input code executes here. Actual pytest item.path observations are separately
verified by scripts/mapping/verify.ps1 on the two accepted Docker candidates.
"""

import json
import subprocess
from dataclasses import asdict, replace

import pytest

from smartregression.adapters.git_local import LocalGit
from smartregression.application.analysis import analyze_execution
from smartregression.application.inventory_store import InventoryConfiguration, prepare_inventory
from smartregression.application.snapshots import RepositoryAuthorization, prepare_snapshots
from smartregression.application.test_mapping import (
    map_inventory_components,
    sources_from_collection,
)
from smartregression.contracts.stages import StageResult
from smartregression.core.execution.inventory import finalize_discovery
from smartregression.core.impact.potential_impact import build_potential_impact
from smartregression.core.selection.mapping import (
    CollectedTestSource,
    MappingSources,
    MappingValidationError,
    inventory_digest,
)


def write_and_receipt(inputs):
    write = prepare_inventory(
        identity=inputs["identity"],
        inventory_id="inventory-1",
        stage=inputs["inventory"],
        configuration=InventoryConfiguration(
            "candidate-inventory/2",
            "owned-mapping-fixture",
            "sha256:" + "a" * 64,
            "b" * 64,
            "c" * 64,
            "d" * 64,
        ),
    )
    identity = replace(
        inputs["test_sources"].identity, configuration_digest=write.configuration_sha256
    )
    receipt = {
        "configuration_sha256": write.configuration_sha256,
        "configuration": json.loads(write.configuration_json),
        "result": {
            "identity": asdict(identity),
            "protocol": "inventory/2",
            "mode": "collect",
            "collection": {
                "ids": write.stage.data.test_ids,
                "exit_code": 0,
                "collection_finished": True,
                "collection_errors": 0,
            },
            "test_sources": {
                "version": "pytest-item-path/1",
                "items": [asdict(s) for s in inputs["test_sources"].sources],
            },
        },
    }
    return write, receipt


def test_structured_receipt_and_frozen_inventory_retain_native_ids_through_json(mapping_inputs):
    inputs = mapping_inputs()
    write, observation = write_and_receipt(inputs)
    receipt = sources_from_collection(write, observation)
    result = map_inventory_components(
        write,
        snapshot=inputs["snapshot"],
        changes=inputs["changes"],
        graph=inputs["graph"],
        impact=inputs["impact"],
        test_sources=receipt,
    )
    restored = json.loads(json.dumps(asdict(result), ensure_ascii=True))
    assert [r["test_id"] for r in restored["relationships"]] == write.stage.data.test_ids
    assert restored["provenance"]["configuration_digest"] == write.configuration_sha256
    assert restored["safe_to_exclude"] is False


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r.update(configuration_sha256="e" * 64),
        lambda r: r["result"].update(identity={}),
        lambda r: r["result"]["test_sources"]["items"][0].update(test_id="unknown"),
        lambda r: r["result"].update(protocol="inventory/1"),
    ],
)
def test_forged_or_legacy_metadata_is_rejected(mapping_inputs, change):
    write, receipt = write_and_receipt(mapping_inputs())
    change(receipt)
    with pytest.raises(MappingValidationError):
        sources_from_collection(write, receipt)


def test_forged_graph_edge_cannot_gain_support_from_schema_alone(mapping_inputs):
    inputs = mapping_inputs()
    write, _ = write_and_receipt(inputs)
    inputs["graph"].data.edges.clear()
    with pytest.raises(MappingValidationError, match="mapping_graph_source_mismatch"):
        map_inventory_components(
            write,
            snapshot=inputs["snapshot"],
            changes=inputs["changes"],
            graph=inputs["graph"],
            impact=inputs["impact"],
        )


def test_real_git_producers_map_changed_function_via_test_file(tmp_path):
    repo = tmp_path / "input"
    repo.mkdir()

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Mapping Fixture")
    git("config", "user.email", "mapping@example.invalid")
    git("config", "core.autocrlf", "false")
    (repo / "tests").mkdir()
    (repo / "logic.py").write_text("def compute():\n    return 1\n")
    (repo / "tests/test_logic.py").write_text(
        "import logic\ndef test_x():\n    raise RuntimeError('never_execute')\n"
    )
    git("add", ".")
    git("commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    (repo / "logic.py").write_text("def compute():\n    return 2\n")
    git("add", ".")
    git("commit", "-qm", "target")
    target = git("rev-parse", "HEAD")
    config = InventoryConfiguration(
        "fixture/1", "owned-mapping-fixture", "sha256:" + "a" * 64, "b" * 64, "c" * 64, "d" * 64
    )

    class Collector:
        configuration_digest = config.digest

        def collect(self, snapshot, *, identity):
            return finalize_discovery(
                expected=identity,
                observed=identity,
                payload={
                    "ids": [" custom native ID[đ] "],
                    "exit_code": 0,
                    "collection_finished": True,
                    "collection_errors": 0,
                },
            )

    execution = analyze_execution(
        LocalGit(repo),
        authorization=RepositoryAuthorization("fixture", repo),
        repository_id="fixture",
        base=base,
        target=target,
        data_kind="demo",
        inventory_collector=Collector(),
    )
    report = execution.report
    impact = StageResult(
        status="completed",
        data=build_potential_impact(
            report.identity, report.stages.changes.data, report.stages.graph.data
        ),
    )
    write = prepare_inventory(
        identity=report.identity,
        inventory_id="inventory-1",
        stage=report.stages.inventory,
        configuration=config,
    )
    from smartregression.application.inventory import inventory_identity

    receipt = MappingSources(
        inventory_identity(report.identity, config.digest),
        write.inventory_id,
        inventory_digest(write.stage),
        (CollectedTestSource(" custom native ID[đ] ", "tests/test_logic.py"),),
    )
    # Reacquire the same authorized Git blobs; AnalysisExecution exposes manifests,
    # not source bytes. A dirty working tree must not substitute for the target.
    (repo / "logic.py").write_text("this is not the committed source\n")
    pair = prepare_snapshots(
        LocalGit(repo),
        authorization=RepositoryAuthorization("fixture", repo),
        repository_id="fixture",
        base=base,
        target=target,
    )
    result = map_inventory_components(
        write,
        snapshot=pair.target,
        changes=report.stages.changes,
        graph=report.stages.graph,
        impact=impact,
        test_sources=receipt,
    )
    components = {c.id: c for c in report.stages.changes.data.components}
    assert any(components[r.changed_component_id].symbol == "compute" for r in result.relationships)
    assert {r.nodes for r in result.relationships} == {("tests/test_logic.py", "logic.py")}
    assert all(r.test_id == " custom native ID[đ] " for r in result.relationships)

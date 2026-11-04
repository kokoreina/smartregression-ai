"""Mapping probes: real collected metadata, explicitly synthetic component seeds.

These are structural relationship fixtures, not an observed Git diff, selected test
set, benchmark cohort or evaluation of fault retention. No input code runs on host.
"""

import argparse
import hashlib
import json
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from smartregression.application.inventory_store import InventoryWrite, validate_inventory_write
from smartregression.application.stage_conversion import graph_result
from smartregression.application.test_mapping import (
    map_inventory_components,
    sources_from_collection,
)
from smartregression.contracts.stages import (
    ChangePayload,
    FileCoverage,
    StageComponent,
    StageResult,
)
from smartregression.core.git.snapshots import (
    TreeEntry,
    canonical_json,
    freeze_snapshot,
    validate_snapshot_paths,
)
from smartregression.core.impact.dependency_graph import build_dependency_graph
from smartregression.core.impact.potential_impact import build_potential_impact
from smartregression.core.selection.mapping import MappingValidationError

ROOT = Path(__file__).resolve().parents[2]
PROBES = {
    "sqlparse": ("sqlparse/lexer.py", {"tests/test_keywords.py", "tests/test_parse.py"}),
    "tinydb": ("tinydb/operations.py", {"tests/test_operations.py", "tests/test_tinydb.py"}),
}


def load_snapshot(folder):
    document = json.loads((folder / "snapshot-manifest.json").read_text())
    validate_snapshot_paths([item["path"] for item in document["files"]])
    entries, contents = [], []
    for item in document["files"]:
        path = folder / "snapshot" / item["path"]
        if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
            raise ValueError("unsafe_mapping_snapshot")
        raw = path.read_bytes()
        entries.append(TreeEntry(item["path"], item["mode"], item["blob_id"], item["size"]))
        contents.append(raw)
    frozen = freeze_snapshot(
        document["repository_id"], document["commit"], tuple(entries), tuple(contents)
    )
    if json.loads(canonical_json(asdict(frozen.manifest))) != document:
        raise ValueError("mapping_snapshot_mismatch")
    return frozen


def execute(evidence_path):
    if any(p.is_symlink() or p.is_junction() for p in (evidence_path, *evidence_path.parents)):
        raise ValueError("unsafe_mapping_evidence")
    evidence_path = evidence_path.resolve(strict=True)
    if not evidence_path.is_relative_to(ROOT / "var"):
        raise ValueError("unsafe_mapping_evidence")
    output = ROOT / "var" / ("mapping-verification-" + uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    ledger = {
        "data_kind": "mapping_probe_with_synthetic_component_seeds",
        "passed": False,
        "started_at": datetime.now(UTC).isoformat(),
        "candidates": {},
        "collection_evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
    }
    try:
        collected = json.loads(evidence_path.read_text())
        if collected["passed"] is not True:
            raise ValueError("collection_not_verified")
        for name, (origin, expected_paths) in PROBES.items():
            folder = evidence_path.parent / name
            snapshot = load_snapshot(folder)
            write = validate_inventory_write(
                InventoryWrite(**json.loads((folder / "inventory-write.json").read_text()))
            )
            receipt = sources_from_collection(write, collected["candidates"][name]["attempts"][0])
            graph = graph_result(
                build_dependency_graph(
                    repository=name,
                    revision=snapshot.manifest.commit,
                    sources={
                        item.path: raw.decode("utf-8")
                        for item, raw in zip(
                            snapshot.manifest.files, snapshot.contents, strict=True
                        )
                        if item.path.endswith(".py")
                    },
                ),
                write.identity.target,
            )
            changes = StageResult[ChangePayload](
                status="completed",
                data=ChangePayload(
                    components=[
                        StageComponent(
                            id="probe-" + name,
                            path=origin,
                            kind="module",
                            change="modified",
                            reason="mapping_probe_fixture",
                        )
                    ],
                    files=[FileCoverage(path=origin, status="completed", limitations=[])],
                ),
            )
            impact = StageResult(
                status=graph.status,
                data=build_potential_impact(write.identity, changes.data, graph.data),
                limitations=graph.limitations,
            )
            result = map_inventory_components(
                write,
                snapshot=snapshot,
                changes=changes,
                graph=graph,
                impact=impact,
                test_sources=receipt,
            )
            by_id = {s.test_id: s.path for s in receipt.sources}
            expected_ids = {node for node, path in by_id.items() if path in expected_paths}
            actual_ids = {r.test_id for r in result.relationships}
            assert expected_ids and actual_ids == expected_ids
            assert {r.test_path for r in result.relationships} == expected_paths
            assert all(
                r.nodes[0] == by_id[r.test_id] and r.nodes[-1] == origin
                for r in result.relationships
            )
            assert all(r.test_id in write.stage.data.test_ids for r in result.relationships)
            assert result.safe_to_exclude is False and result.status == "partial"
            try:
                map_inventory_components(
                    write,
                    snapshot=snapshot,
                    changes=changes,
                    graph=graph,
                    impact=impact,
                    test_sources=replace(receipt, inventory_id="stale-inventory"),
                )
            except MappingValidationError:
                rejected = True
            else:
                rejected = False
            assert rejected
            raw = canonical_json(asdict(result))
            (output / (name + "-mapping.json")).write_bytes(raw)
            ledger["candidates"][name] = {
                "component_seed_fixture": origin,
                "expected_test_files": sorted(expected_paths),
                "collection_count": len(write.stage.data.test_ids),
                "mapped_native_ids": len(actual_ids),
                "relationships": len(result.relationships),
                "mapping_status": result.status,
                "unresolved": len(result.unresolved),
                "source_receipt_digest": result.provenance.test_sources_digest,
                "mapping_sha256": hashlib.sha256(raw).hexdigest(),
                "stale_receipt_rejected": rejected,
            }
        ledger["passed"] = True
    except Exception as exc:
        ledger["error_type"] = type(exc).__name__
        ledger["error_code"] = "mapping_verification_failed"
    finally:
        ledger["finished_at"] = datetime.now(UTC).isoformat()
        (output / "evidence.json").write_bytes(canonical_json(ledger))
        print(json.dumps({"passed": ledger["passed"], "evidence": str(output / "evidence.json")}))
    return 0 if ledger["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-evidence", type=Path, required=True)
    raise SystemExit(execute(parser.parse_args().collection_evidence))

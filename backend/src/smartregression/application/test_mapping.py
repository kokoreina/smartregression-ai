"""Explicit mapping use case; neither starts a worker nor modifies public reports."""

import json
from dataclasses import asdict

from smartregression.application.inventory import inventory_identity, inventory_stage
from smartregression.application.inventory_store import InventoryWrite, validate_inventory_write
from smartregression.application.stage_conversion import graph_result
from smartregression.contracts.stages import (
    ChangePayload,
    EvidencePayload,
    GraphPayload,
    ImpactPayload,
    StageResult,
)
from smartregression.core.execution.inventory import finalize_discovery
from smartregression.core.git.snapshots import FrozenSnapshot, validate_frozen_snapshot
from smartregression.core.impact.dependency_graph import build_dependency_graph
from smartregression.core.selection.mapping import (
    CollectedTestSource,
    ComponentTestMapping,
    MappingSources,
    MappingValidationError,
    build_component_test_mapping,
    inventory_digest,
)


def sources_from_collection(write: InventoryWrite, observation: dict) -> MappingSources:
    """Validate a trusted adapter receipt; accepting arbitrary JSON is not authorization.

    Legacy inventory-only receipts cannot recover file provenance from nodeid text.
    Callers must recollect using the item.path observer, or keep mappings unresolved.
    """
    write = validate_inventory_write(write)
    try:
        expected = inventory_identity(write.identity, write.configuration_sha256)
        result = observation["result"]
        if (
            write.stage.data is None
            or observation["configuration_sha256"] != write.configuration_sha256
            or observation["configuration"] != json.loads(write.configuration_json)
            or result["protocol"] != "inventory/2"
            or result["mode"] != "collect"
            or result["identity"] != asdict(expected)
        ):
            raise MappingValidationError("mapping_collection_receipt_mismatch")
        discovered = finalize_discovery(
            expected=expected, observed=expected, payload=result["collection"]
        )
        if inventory_stage(discovered, write.identity) != write.stage:
            raise MappingValidationError("mapping_collection_receipt_mismatch")
        metadata = result["test_sources"]
        if (
            type(metadata) is not dict
            or set(metadata) != {"version", "items"}
            or metadata["version"] != "pytest-item-path/1"
            or type(metadata["items"]) is not list
        ):
            raise MappingValidationError("invalid_mapping_collection_metadata")
        sources = []
        for item in metadata["items"]:
            if type(item) is not dict or set(item) != {"test_id", "path"}:
                raise MappingValidationError("invalid_mapping_collection_metadata")
            if (
                type(item["test_id"]) is not str
                or item["path"] is not None
                and type(item["path"]) is not str
            ):
                raise MappingValidationError("invalid_mapping_collection_metadata")
            sources.append(CollectedTestSource(item["test_id"], item["path"]))
        if [item.test_id for item in sources] != write.stage.data.test_ids:
            raise MappingValidationError("mapping_collection_receipt_mismatch")
        return MappingSources(
            expected, write.inventory_id, inventory_digest(write.stage), tuple(sources)
        )
    except MappingValidationError:
        raise
    except ValueError, TypeError, KeyError, AttributeError:
        raise MappingValidationError("invalid_mapping_collection_metadata") from None


def _check_graph_source(snapshot, graph):
    if graph.data is None:
        return
    try:
        declared = GraphPayload.model_validate(graph.data.model_dump())
        sources = {}
        for item, raw in zip(snapshot.manifest.files, snapshot.contents, strict=True):
            if not item.path.endswith(".py"):
                continue
            if len(raw) > 256_000 or b"\0" in raw:
                raise MappingValidationError("mapping_graph_source_mismatch")
            sources[item.path] = raw.decode("utf-8")
        actual = graph_result(
            build_dependency_graph(
                repository=snapshot.manifest.repository_id,
                revision=snapshot.manifest.commit,
                sources=sources,
            ),
            declared.snapshot,
        ).data

        # Collection/order changes do not create a different graph relation.
        def signature(data):
            return (
                data.snapshot,
                set(data.nodes),
                {(e.source, e.target, e.kind) for e in data.edges},
                {(u.source_path, u.reference, u.kind, u.reason) for u in data.unresolved},
            )

        if signature(actual) != signature(declared):
            raise MappingValidationError("mapping_graph_source_mismatch")
    except MappingValidationError:
        raise
    except ValueError, TypeError, AttributeError, UnicodeError:
        raise MappingValidationError("mapping_graph_source_mismatch") from None


def map_inventory_components(
    write: InventoryWrite,
    *,
    snapshot: FrozenSnapshot,
    changes: StageResult[ChangePayload],
    graph: StageResult[GraphPayload],
    impact: StageResult[ImpactPayload],
    test_sources: MappingSources | None = None,
    evidence: EvidencePayload | None = None,
) -> ComponentTestMapping:
    """Map one immutable run inventory with actual frozen graph sources.

    Changes/impact must come from this run's authorized upstream producers. This
    checks their structural references, not that a client-authored diff was genuine.
    It does not perform test selection, dispatch, fallback or hidden host collection.
    """
    write = validate_inventory_write(write)
    validate_frozen_snapshot(snapshot)
    _check_graph_source(snapshot, graph)
    return build_component_test_mapping(
        identity=write.identity,
        snapshot=snapshot,
        inventory_id=write.inventory_id,
        configuration_digest=write.configuration_sha256,
        changes=changes,
        graph=graph,
        impact=impact,
        inventory=write.stage,
        test_sources=test_sources,
        evidence=evidence,
    )

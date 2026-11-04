"""Static positive relationships only; no selection, exclusion or input-code execution."""

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Literal

from pydantic import ValidationError

from smartregression.contracts.stages import (
    ChangePayload,
    EvidencePayload,
    GraphPayload,
    ImpactPayload,
    InventoryPayload,
    RunIdentity,
    StageResult,
    validate_artifacts,
)
from smartregression.core.execution.inventory import InventoryIdentity
from smartregression.core.git.snapshots import (
    FrozenSnapshot,
    canonical_json,
    validate_frozen_snapshot,
    validate_snapshot_paths,
)

RULE_VERSION = "pytest-import-file/1"
MAX_RELATIONSHIPS = 50_000


class MappingValidationError(ValueError):
    """Safe stable code; raw test IDs and source are never exception messages."""


def _digest(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def inventory_digest(stage: StageResult[InventoryPayload]) -> str:
    return _digest(stage.model_dump(mode="json"))


@dataclass(frozen=True)
class CollectedTestSource:
    test_id: str
    path: str | None


@dataclass(frozen=True)
class MappingSources:
    """Trusted collector receipt, not proof that arbitrary callers ran a collector.

    Only explicit observed paths are used. None means metadata unavailable; nodeid
    syntax, names, docstrings or parameter text never substitute for a file path.
    """

    identity: InventoryIdentity
    inventory_id: str
    inventory_digest: str
    sources: tuple[CollectedTestSource, ...]
    observer_version: str = "pytest-item-path/1"


@dataclass(frozen=True)
class TestRelationship:
    changed_component_id: str
    test_id: str
    test_path: str
    candidate_id: str
    impact_path_id: str | None
    nodes: tuple[str, ...]
    relationship: Literal["changed", "direct", "indirect"]
    granularity: Literal["test_file_to_component_module"] = "test_file_to_component_module"


@dataclass(frozen=True)
class UnresolvedMapping:
    reason: str
    changed_component_id: str | None = None
    test_id: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class MappingProvenance:
    repository_id: str
    run_id: str
    target_commit: str
    snapshot_id: str
    inventory_id: str
    configuration_digest: str
    inventory_digest: str
    changes_digest: str
    graph_digest: str
    impact_digest: str
    test_sources_digest: str | None
    rule_version: str = RULE_VERSION


@dataclass(frozen=True)
class ComponentTestMapping:
    provenance: MappingProvenance
    status: Literal["completed", "partial", "failed", "not_run"]
    relationships: tuple[TestRelationship, ...]
    unresolved: tuple[UnresolvedMapping, ...]
    schema_version: Literal["component-test-mapping/1"] = field(
        default="component-test-mapping/1", init=False
    )
    safe_to_exclude: Literal[False] = field(default=False, init=False)


def _checked_sources(receipt, identity, inventory_id, config_digest, inventory):
    if receipt is None:
        return {}
    expected = InventoryIdentity(
        identity.repository_id,
        identity.run_id,
        identity.target.commit,
        identity.target.snapshot_id,
        config_digest,
    )
    if (
        not isinstance(receipt, MappingSources)
        or receipt.identity != expected
        or receipt.inventory_id != inventory_id
        or receipt.inventory_digest != inventory_digest(inventory)
        or receipt.observer_version != "pytest-item-path/1"
        or type(receipt.sources) is not tuple
    ):
        raise MappingValidationError("mapping_source_identity_mismatch")
    ids = set(inventory.data.test_ids) if inventory.data else set()
    paths = {}
    for item in receipt.sources:
        if (
            not isinstance(item, CollectedTestSource)
            or type(item.test_id) is not str
            or item.test_id not in ids
            or item.test_id in paths
        ):
            raise MappingValidationError("unknown_or_duplicate_mapping_test_id")
        if item.path is not None:
            if type(item.path) is not str:
                raise MappingValidationError("invalid_test_source_path")
            validate_snapshot_paths([item.path])
        paths[item.test_id] = item.path
    return paths


def build_component_test_mapping(
    *,
    identity: RunIdentity,
    snapshot: FrozenSnapshot,
    inventory_id: str,
    configuration_digest: str,
    changes: StageResult[ChangePayload],
    graph: StageResult[GraphPayload],
    impact: StageResult[ImpactPayload],
    inventory: StageResult[InventoryPayload],
    test_sources: MappingSources | None = None,
    evidence: EvidencePayload | None = None,
) -> ComponentTestMapping:
    """Bind supported impact paths to explicitly observed files of existing tests.

    Trust: caller supplies authorized frozen sources and collector metadata. Models
    and hashes prevent accidental drift, not a hostile caller forging all inputs.
    File import reachability says nothing about which test function calls a symbol.
    """
    try:
        identity = RunIdentity.model_validate(identity.model_dump())
        validate_frozen_snapshot(snapshot)
        manifest = snapshot.manifest
        if (manifest.repository_id, manifest.commit, manifest.snapshot_id) != (
            identity.repository_id,
            identity.target.commit,
            identity.target.snapshot_id,
        ):
            raise MappingValidationError("mapping_target_mismatch")
        if (
            type(inventory_id) is not str
            or not inventory_id
            or inventory_id != inventory_id.strip()
            or "\0" in inventory_id
            or len(inventory_id.encode()) > 512
            or type(configuration_digest) is not str
            or not re.fullmatch(r"[0-9a-f]{64}", configuration_digest)
        ):
            raise MappingValidationError("invalid_mapping_provenance")
        changes = StageResult[ChangePayload].model_validate(changes.model_dump())
        graph = StageResult[GraphPayload].model_validate(graph.model_dump())
        impact = StageResult[ImpactPayload].model_validate(impact.model_dump())
        inventory = StageResult[InventoryPayload].model_validate(inventory.model_dump())
        evidence = EvidencePayload.model_validate(evidence.model_dump()) if evidence else None
        for stage in (graph, impact, inventory):
            if stage.data is not None and stage.data.snapshot != identity.target:
                raise MappingValidationError("mapping_requires_target_payloads")
        if inventory.data and (
            (inventory.status == "partial") != (inventory.data.completeness == "partial")
        ):
            raise MappingValidationError("mapping_inventory_state_mismatch")
        if graph.data and graph.data.unresolved and graph.status != "partial":
            raise MappingValidationError("mapping_graph_state_mismatch")
        if (
            changes.data
            and any(f.status != "completed" or f.limitations for f in changes.data.files)
            and changes.status != "partial"
        ):
            raise MappingValidationError("mapping_changes_state_mismatch")
        paths = _checked_sources(
            test_sources, identity, inventory_id, configuration_digest, inventory
        )
        provenance = MappingProvenance(
            identity.repository_id,
            identity.run_id,
            identity.target.commit,
            identity.target.snapshot_id,
            inventory_id,
            configuration_digest,
            inventory_digest(inventory),
            _digest(changes.model_dump(mode="json")),
            _digest(graph.model_dump(mode="json")),
            _digest(impact.model_dump(mode="json")),
            _digest(asdict(test_sources)) if test_sources else None,
        )
        issues = []
        stages = {"changes": changes, "graph": graph, "impact": impact, "inventory": inventory}
        for name, stage in stages.items():
            if stage.status not in {"completed", "partial"}:
                issues.append(
                    UnresolvedMapping(f"{name}_{stage.error_code or stage.reason or stage.status}")
                )
            issues.extend(
                UnresolvedMapping(f"{name}_{issue.code}", path=issue.path)
                for issue in stage.limitations
            )
        if any(s.data is None for s in stages.values()):
            return ComponentTestMapping(
                provenance,
                "failed" if any(s.status == "failed" for s in stages.values()) else "not_run",
                (),
                tuple(issues),
            )
        validate_artifacts(identity, changes.data, graph.data, impact.data, evidence)
        snapshot_paths = {f.path for f in manifest.files}
        if not set(graph.data.nodes) <= snapshot_paths:
            raise MappingValidationError("graph_node_not_in_target")
        # Scope validation is structural; producer/source correctness remains the
        # upstream responsibility. Unknown graph kinds are not support for mapping.
        supported_kinds = {"absolute_import", "relative_import"}
        edges = {(e.source, e.target) for e in graph.data.edges if e.kind in supported_kinds}
        path_records = {p.id: p for p in impact.data.paths}
        candidates = {}
        for candidate in impact.data.candidates:
            candidates.setdefault(candidate.path, []).append(candidate)
        relationships = []
        mapped_components = set()
        for node_id in inventory.data.test_ids:
            path = paths.get(node_id)
            reason = (
                "test_source_unavailable"
                if path is None
                else "test_source_not_in_snapshot"
                if path not in snapshot_paths
                else "test_source_not_in_graph"
                if path not in graph.data.nodes
                else None
            )
            if reason:
                issues.append(UnresolvedMapping(reason, test_id=node_id, path=path))
                continue
            before = len(relationships)
            for candidate in sorted(candidates.get(path, []), key=lambda c: c.id):
                routes = (
                    [(None, (path,))]
                    if candidate.relationship == "changed"
                    else [
                        (pid, tuple(path_records[pid].nodes)) for pid in sorted(candidate.path_ids)
                    ]
                )
                for pid, nodes in routes:
                    if any((a, b) not in edges for a, b in zip(nodes, nodes[1:], strict=False)):
                        issues.append(
                            UnresolvedMapping(
                                "unsupported_graph_edge_kind",
                                candidate.changed_component_id,
                                node_id,
                                path,
                            )
                        )
                        continue
                    if len(relationships) >= MAX_RELATIONSHIPS:
                        raise MappingValidationError("mapping_relationship_limit")
                    relationships.append(
                        TestRelationship(
                            candidate.changed_component_id,
                            node_id,
                            path,
                            candidate.id,
                            pid,
                            nodes,
                            candidate.relationship,
                        )
                    )
                    mapped_components.add(candidate.changed_component_id)
            if len(relationships) == before:
                issues.append(
                    UnresolvedMapping("no_supported_test_relationship", test_id=node_id, path=path)
                )
        for component in sorted(changes.data.components, key=lambda c: c.id):
            if component.id not in mapped_components:
                issues.append(
                    UnresolvedMapping(
                        "component_deleted_no_target"
                        if component.change == "deleted"
                        else "component_has_no_supported_test",
                        changed_component_id=component.id,
                        path=component.path,
                    )
                )
        issues.extend(
            UnresolvedMapping("graph_" + u.reason, path=u.source_path)
            for u in graph.data.unresolved
        )
        issues = list(dict.fromkeys(issues))
        status = (
            "partial"
            if issues or any(s.status == "partial" for s in stages.values())
            else "completed"
        )
        return ComponentTestMapping(provenance, status, tuple(relationships), tuple(issues))
    except MappingValidationError:
        raise
    except ValueError, TypeError, AttributeError, KeyError, UnicodeError, ValidationError:
        raise MappingValidationError("invalid_mapping_input") from None

"""Run/report-bound mapping sidecars from actual stages and trusted collection receipts."""

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Protocol

from smartregression.application.inventory import InventoryCollector
from smartregression.application.inventory_store import InventoryConfiguration, prepare_inventory
from smartregression.application.run_store import ReportArtifact
from smartregression.application.test_mapping import (
    map_inventory_components,
    sources_from_collection,
)
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.git.snapshots import FrozenSnapshot, canonical_json

MAX_MAPPING_BYTES = 16 * 1024 * 1024


class MappingCollector(InventoryCollector, Protocol):
    @property
    def configuration(self) -> InventoryConfiguration: ...

    @property
    def last_observation(self) -> dict: ...


@dataclass(frozen=True)
class MappingArtifact:
    """Producer bytes plus a descriptor; not permission to select/dispatch tests."""

    raw: bytes
    descriptor: ReportArtifact


def prepare_mapping_artifact(
    report: StageAnalysisReport,
    snapshot: FrozenSnapshot,
    collector: MappingCollector,
    *,
    configuration_digest: str,
) -> MappingArtifact:
    """Caller owns acquisition and injects the live collector, not receipt JSON.

    Failures retain failed/not_run mapping states. A successful/partial inventory
    requires an exact item.path receipt from the same collection and configuration.
    """
    report = StageAnalysisReport.model_validate_json(report.model_dump_json())
    configuration = collector.configuration
    if (
        not isinstance(configuration, InventoryConfiguration)
        or configuration.digest != configuration_digest
        or collector.configuration_digest != configuration_digest
    ):
        raise ValueError("mapping_configuration_mismatch")
    write = prepare_inventory(
        identity=report.identity,
        inventory_id=report.identity.run_id + "-inventory",
        stage=report.stages.inventory,
        configuration=configuration,
    )
    receipt = (
        sources_from_collection(write, collector.last_observation)
        if write.stage.data is not None
        else None
    )
    mapping = map_inventory_components(
        write,
        snapshot=snapshot,
        changes=report.stages.changes,
        graph=report.stages.graph,
        impact=report.stages.impact,
        test_sources=receipt,
        evidence=report.stages.evidence.data,
    )
    report_raw = report.model_dump_json(indent=2).encode("utf-8") + b"\n"
    raw = canonical_json(
        {
            "schema_version": "report-mapping/1",
            "identity": report.identity.model_dump(mode="json"),
            "report_id": report.report_id,
            "report_sha256": hashlib.sha256(report_raw).hexdigest(),
            "mapping": asdict(mapping),
        }
    )
    if len(raw) > MAX_MAPPING_BYTES:
        raise ValueError("mapping_artifact_limit")
    return MappingArtifact(
        raw,
        ReportArtifact(
            report.report_id + "-mapping",
            f"{report.identity.run_id}/{report.report_id}.mapping.json",
            hashlib.sha256(raw).hexdigest(),
            len(raw),
        ),
    )


def verify_mapping_artifact(
    raw: bytes, *, expected: MappingArtifact, report: StageAnalysisReport
) -> dict:
    """Compare with trusted producer output; serialized sidecars cannot authorize.

    A consumer without live producer output must recompute mapping using authorized
    sources/receipts. Merely parsing a sidecar/digest is not semantic verification.
    """
    try:
        report = StageAnalysisReport.model_validate_json(report.model_dump_json())
        report_raw = report.model_dump_json(indent=2).encode("utf-8") + b"\n"
        if (
            not isinstance(raw, bytes)
            or not 0 < len(raw) <= MAX_MAPPING_BYTES
            or len(raw) != expected.descriptor.size_bytes
            or hashlib.sha256(raw).hexdigest() != expected.descriptor.sha256
            or raw != expected.raw
        ):
            raise ValueError("mapping_artifact_mismatch")
        document = json.loads(raw)
        if (
            document["schema_version"] != "report-mapping/1"
            or document["identity"] != report.identity.model_dump(mode="json")
            or document["report_id"] != report.report_id
            or document["report_sha256"] != hashlib.sha256(report_raw).hexdigest()
            or canonical_json(document) != raw
        ):
            raise ValueError("mapping_artifact_mismatch")
        return document
    except ValueError, TypeError, KeyError, AttributeError:
        raise ValueError("mapping_artifact_mismatch") from None

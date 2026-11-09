"""A concrete compound writer: report catalog and optional evidence share one commit."""

import hashlib
import json

import sqlalchemy as sa

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.evidence_store import BoundEvidenceStore
from smartregression.adapters.storage.inventory_store import BoundInventoryStore
from smartregression.adapters.storage.run_store import BoundRunReportStore
from smartregression.application.evidence_store import (
    EVIDENCE_FORMAT,
    decode_evidence,
    prepare_evidence,
)
from smartregression.application.inventory_store import InventoryWrite, validate_inventory_write
from smartregression.application.persistence import bundle_from_report, check_bundle_overlap
from smartregression.application.run_store import (
    RunMetadataError,
    RunReportWrite,
    validate_run_report_write,
)
from smartregression.contracts.stages import StageAnalysisReport


class PostgresAnalysisStore:
    """Capture immutable preflight bytes before publication; no DB connection in init."""

    def __init__(
        self,
        engine: sa.Engine,
        report: StageAnalysisReport,
        *,
        inventory: InventoryWrite | None = None,
    ) -> None:
        self.engine = engine
        checked = StageAnalysisReport.model_validate_json(report.model_dump_json())
        self.report_bytes = checked.model_dump_json(indent=2).encode("utf-8") + b"\n"
        bundle = bundle_from_report(checked)
        self.bundle_bytes = prepare_evidence(bundle) if bundle is not None else None
        self.inventory = validate_inventory_write(inventory) if inventory is not None else None
        if self.inventory is not None and (
            self.inventory.identity != checked.identity
            or self.inventory.stage != checked.stages.inventory
            or self.inventory.inventory_id != checked.identity.run_id + "-inventory"
        ):
            raise RunMetadataError()

    def save(self, write: RunReportWrite) -> None:
        write = validate_run_report_write(write)
        report = StageAnalysisReport.model_validate_json(self.report_bytes)
        if (
            report.identity != write.identity
            or report.report_id != write.report_id
            or hashlib.sha256(self.report_bytes).hexdigest() != write.artifact.sha256
            or len(self.report_bytes) != write.artifact.size_bytes
        ):
            raise RunMetadataError()
        bundle = (
            None
            if self.bundle_bytes is None
            else decode_evidence(
                self.bundle_bytes,
                EVIDENCE_FORMAT,
                hashlib.sha256(self.bundle_bytes).hexdigest(),
                write.identity,
            )
        )
        if bundle is not None:
            check_bundle_overlap(report, bundle)
        if self.inventory is not None and (
            self.inventory.configuration_sha256
            != json.loads(write.configuration_json).get("inventory_configuration_digest")
        ):
            raise RunMetadataError()
        with database_transaction(self.engine) as connection:
            evidence_store = BoundEvidenceStore(connection)
            existing = evidence_store.load(write.identity)
            if existing is not None:
                check_bundle_overlap(report, existing)
            BoundRunReportStore(connection).save(write)
            if bundle is not None:
                evidence_store.save(bundle)
            if self.inventory is not None:
                BoundInventoryStore(connection).save(self.inventory)

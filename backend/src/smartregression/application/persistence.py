"""Explicit publish-then-save use case; no DB/FS imports or automatic workflow side effects."""

import hashlib
from typing import Protocol

from smartregression.application.evidence_store import EvidenceConflict, prepare_evidence
from smartregression.application.run_store import (
    ReportArtifact,
    RunConfiguration,
    RunMetadataError,
    RunReportStore,
    RunReportWrite,
    prepare_run_report,
    validate_run_report_write,
)
from smartregression.contracts.stages import EvidenceBundle, StageAnalysisReport
from smartregression.core.git.snapshots import SnapshotManifest


class ReportPublisher(Protocol):
    def publish(self, artifact: ReportArtifact, raw: bytes) -> None: ...


def bundle_from_report(report: StageAnalysisReport) -> EvidenceBundle | None:
    """Never synthesize empty payloads for unavailable stages."""
    checked = StageAnalysisReport.model_validate_json(report.model_dump_json())
    values = {
        name: getattr(checked.stages, name).data
        for name in ("changes", "graph", "impact", "evidence")
    }
    if any(value is None for value in values.values()):
        return None
    return EvidenceBundle(identity=checked.identity, **values)


def check_bundle_overlap(report: StageAnalysisReport, bundle: EvidenceBundle) -> None:
    if report.identity != bundle.identity or any(
        getattr(report.stages, name).data is not None
        and getattr(report.stages, name).data != getattr(bundle, name)
        for name in ("changes", "graph", "impact", "evidence")
    ):
        raise EvidenceConflict()


def persist_report(
    publisher: ReportPublisher,
    store: RunReportStore,
    *,
    report: StageAnalysisReport,
    configuration: RunConfiguration,
    snapshot_manifests: tuple[SnapshotManifest, ...],
    artifact_id: str,
    storage_key: str,
    bundle: EvidenceBundle | None = None,
) -> RunReportWrite:
    """Caller authorizes source/artifact root and supplies verified acquisition metadata.

    No DB call follows publication failure. DB/ambiguous-commit failure preserves
    the complete published file for reconciliation; never delete a possibly used file.
    """
    try:
        report = StageAnalysisReport.model_validate_json(report.model_dump_json())
    except ValueError, TypeError, AttributeError:
        raise RunMetadataError() from None
    if bundle is not None:
        expected = bundle_from_report(report)
        if expected is None or prepare_evidence(expected) != prepare_evidence(bundle):
            raise EvidenceConflict()
    raw = report.model_dump_json(indent=2).encode("utf-8") + b"\n"
    artifact = ReportArtifact(artifact_id, storage_key, hashlib.sha256(raw).hexdigest(), len(raw))
    write = validate_run_report_write(
        prepare_run_report(
            report=report,
            configuration=configuration,
            snapshot_manifests=snapshot_manifests,
            artifact=artifact,
            published_report_bytes=raw,
        )
    )
    publisher.publish(artifact, raw)
    store.save(write)
    return write

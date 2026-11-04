"""Explicit publish-then-save use case; no DB/FS imports or automatic workflow side effects."""

import hashlib
from typing import Protocol

from smartregression.application.run_store import (
    ReportArtifact,
    RunConfiguration,
    RunReportStore,
    RunReportWrite,
    prepare_run_report,
    validate_run_report_write,
)
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.git.snapshots import SnapshotManifest


class ReportPublisher(Protocol):
    def publish(self, artifact: ReportArtifact, raw: bytes) -> None: ...


def persist_report(
    publisher: ReportPublisher,
    store: RunReportStore,
    *,
    report: StageAnalysisReport,
    configuration: RunConfiguration,
    snapshot_manifests: tuple[SnapshotManifest, ...],
    artifact_id: str,
    storage_key: str,
) -> RunReportWrite:
    """Caller authorizes source/artifact root and supplies verified acquisition metadata.

    No DB call follows publication failure. DB/ambiguous-commit failure preserves
    the complete published file for reconciliation; never delete a possibly used file.
    """
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

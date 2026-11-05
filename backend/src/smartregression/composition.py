"""Local CLI composition; no Git/filesystem adapters leak into application logic."""

from pathlib import Path
from typing import Literal

from smartregression.adapters.git_local import LocalGit
from smartregression.application.analysis import analyze_execution
from smartregression.application.inventory import InventoryCollector
from smartregression.application.mapping_artifact import MappingCollector, verify_mapping_artifact
from smartregression.application.persistence import bundle_from_report, persist_report
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.contracts.stages import StageAnalysisReport


def analyze_local(
    *,
    repository: Path,
    repository_id: str,
    authorized_root: Path,
    base: str,
    target: str,
    data_kind: Literal["demo", "real"],
    artifact_root: Path | None = None,
    inventory_collector: InventoryCollector | None = None,
    mapping_collector: MappingCollector | None = None,
    mapping_artifact_root: Path | None = None,
    index_root: Path | None = None,
) -> StageAnalysisReport:
    source = LocalGit(repository)
    mapping_publisher = None
    if mapping_collector is not None:
        from smartregression.adapters.storage.report_publication import ReportFiles

        mapping_root = mapping_artifact_root or artifact_root
        if mapping_root is None:
            raise ValueError("mapping_artifact_root_required")
        mapping_publisher = ReportFiles(mapping_root, source_repository=source.repository)
    elif mapping_artifact_root is not None:
        raise ValueError("mapping_collector_required")
    retrieval_store = None
    if index_root is not None:
        from smartregression.adapters.storage.config import load_database_settings
        from smartregression.adapters.storage.lexical_index import (
            ConfiguredLexicalStore,
            IndexFiles,
        )

        retrieval_store = ConfiguredLexicalStore(
            load_database_settings(), IndexFiles(index_root, source_repository=source.repository)
        )
    if artifact_root is not None:
        # Keep CLI help/default analysis independent even of loading DB infrastructure.
        from smartregression.adapters.storage.analysis_store import PostgresAnalysisStore
        from smartregression.adapters.storage.config import load_database_settings
        from smartregression.adapters.storage.connection import database_engine
        from smartregression.adapters.storage.report_publication import ReportFiles

        settings = load_database_settings()
        publisher = ReportFiles(artifact_root, source_repository=source.repository)
    execution = analyze_execution(
        source,
        authorization=RepositoryAuthorization(repository_id, authorized_root),
        repository_id=repository_id,
        base=base,
        target=target,
        data_kind=data_kind,
        inventory_collector=inventory_collector,
        mapping_collector=mapping_collector,
        retrieval_store=retrieval_store,
    )
    report = StageAnalysisReport.model_validate_json(execution.report.model_dump_json())
    if mapping_publisher is not None:
        sidecar = execution.mapping_artifact
        if sidecar is None:
            from smartregression.application.run_store import RunMetadataError

            raise RunMetadataError()
        verify_mapping_artifact(sidecar.raw, expected=sidecar, report=report)
        # Same guarded immutable byte publisher; ReportFiles.read stays report-only.
        # Preserve this complete sidecar if subsequent report/DB publication fails.
        mapping_publisher.publish(sidecar.descriptor, sidecar.raw)
    if artifact_root is not None:
        with database_engine(settings) as engine:
            persist_report(
                publisher,
                PostgresAnalysisStore(engine, report),
                report=report,
                configuration=execution.configuration,
                snapshot_manifests=execution.snapshot_manifests,
                artifact_id=report.report_id,
                storage_key=f"{report.identity.run_id}/{report.report_id}.json",
                bundle=bundle_from_report(report),
            )
    return report

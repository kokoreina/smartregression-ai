"""Local CLI composition; no Git/filesystem adapters leak into application logic."""

import re
from contextlib import ExitStack
from pathlib import Path
from typing import Literal

from smartregression.adapters.git_local import LocalGit
from smartregression.application.analysis import analyze_execution
from smartregression.application.inventory import InventoryCollector
from smartregression.application.inventory_store import prepare_inventory
from smartregression.application.mapping_artifact import MappingCollector, verify_mapping_artifact
from smartregression.application.persistence import bundle_from_report, persist_report
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.contracts.stages import StageAnalysisReport


def _candidate_collector(
    *,
    name: str,
    image: str | None,
    workspace: Path | None,
    repository: Path,
    repository_id: str,
    target: str,
) -> MappingCollector:
    from smartregression.adapters.runners.candidate_inventory import (
        CANDIDATES,
        CandidateInventoryCollector,
    )

    if (
        name not in CANDIDATES
        or repository_id != name
        or target != CANDIDATES[name][1]
        or image is None
        or re.fullmatch(r"sha256:[0-9a-f]{64}", image) is None
        or workspace is None
    ):
        raise ValueError("invalid_inventory_arguments")
    if any(p.is_symlink() or p.is_junction() for p in (workspace, *workspace.parents)):
        raise ValueError("invalid_inventory_arguments")
    source, worker = repository.resolve(strict=True), workspace.resolve(strict=True)
    if worker.is_relative_to(source) or source.is_relative_to(worker) or not worker.is_dir():
        raise ValueError("invalid_inventory_arguments")
    # This opt-in runs the trusted observer shipped in the source checkout, never
    # scripts selected from the input repository. The collector hashes that observer.
    return CandidateInventoryCollector(name, image, Path(__file__).resolve().parents[3], worker)


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
    inventory_candidate: str | None = None,
    inventory_image: str | None = None,
    inventory_workspace: Path | None = None,
    index_artifact_root: Path | None = None,
) -> StageAnalysisReport:
    if index_artifact_root is not None and artifact_root is None:
        raise ValueError("invalid_retrieval_arguments")
    if inventory_candidate is not None:
        if (
            inventory_collector is not None
            or mapping_collector is not None
            or (mapping_artifact_root is None and artifact_root is None)
        ):
            raise ValueError("invalid_inventory_arguments")
        mapping_collector = _candidate_collector(
            name=inventory_candidate,
            image=inventory_image,
            workspace=inventory_workspace,
            repository=repository,
            repository_id=repository_id,
            target=target,
        )
    elif (
        inventory_image is not None
        or inventory_workspace is not None
        or (mapping_artifact_root is not None and mapping_collector is None)
    ):
        raise ValueError("invalid_inventory_arguments")
    with ExitStack() as stack:
        source = (
            LocalGit(repository, cache_bytes=64 * 1024 * 1024)
            if index_artifact_root is not None
            else LocalGit(repository)
        )
        engine = None
        retrieval_store = None
        mapping_publisher = None
        if mapping_collector is not None:
            from smartregression.adapters.storage.report_publication import ReportFiles

            mapping_root = mapping_artifact_root or artifact_root
            if mapping_root is None:
                raise ValueError("mapping_artifact_root_required")
            mapping_publisher = ReportFiles(mapping_root, source_repository=source.repository)
        elif mapping_artifact_root is not None:
            raise ValueError("mapping_collector_required")
        if artifact_root is not None:
            # Keep CLI help/default analysis independent even of loading DB infrastructure.
            from smartregression.adapters.storage.analysis_store import PostgresAnalysisStore
            from smartregression.adapters.storage.config import load_database_settings
            from smartregression.adapters.storage.connection import database_engine
            from smartregression.adapters.storage.report_publication import ReportFiles

            settings = load_database_settings()
            publisher = ReportFiles(artifact_root, source_repository=source.repository)
            if index_artifact_root is not None:
                from smartregression.adapters.storage.index_artifacts import IndexArtifactFiles
                from smartregression.adapters.storage.index_store import PostgresIndexStore
                from smartregression.application.retrieval import PublishedLexicalIndex

                index_files = IndexArtifactFiles(
                    index_artifact_root, source_repository=source.repository
                )
                engine = stack.enter_context(database_engine(settings))
                retrieval_store = PublishedLexicalIndex(
                    source,
                    authorization=RepositoryAuthorization(repository_id, authorized_root),
                    store=PostgresIndexStore(engine),
                    artifacts=index_files,
                )
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
        inventory = None
        if artifact_root is not None and mapping_collector is not None:
            inventory = prepare_inventory(
                identity=report.identity,
                inventory_id=report.identity.run_id + "-inventory",
                stage=report.stages.inventory,
                configuration=mapping_collector.configuration,
            )
            if (
                inventory.configuration_sha256
                != execution.configuration.inventory_configuration_digest
            ):
                raise ValueError("mapping_configuration_mismatch")
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
            if engine is None:
                engine = stack.enter_context(database_engine(settings))
            persist_report(
                publisher,
                PostgresAnalysisStore(engine, report, inventory=inventory),
                report=report,
                configuration=execution.configuration,
                snapshot_manifests=execution.snapshot_manifests,
                artifact_id=report.report_id,
                storage_key=f"{report.identity.run_id}/{report.report_id}.json",
                bundle=bundle_from_report(report),
            )
        return report

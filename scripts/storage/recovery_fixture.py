"""Quiescent, task-owned report/file fixture for the backup/restore drill.

This is direct foundation test setup, not H1's production RunReportStore adapter.
"""

import hashlib
import json
import os
from pathlib import Path

from sqlalchemy import Connection

from smartregression.adapters.storage.schema import (
    analysis_runs,
    artifacts,
    repositories,
    run_reports,
    snapshots,
)
from smartregression.application.analysis import aggregate_status
from smartregression.application.run_store import (
    ReportArtifact,
    RunConfiguration,
    prepare_run_report,
)
from smartregression.application.stage_conversion import identity_from_snapshots, snapshots_result
from smartregression.contracts.stages import AnalysisStages, StageAnalysisReport, StageResult
from smartregression.core.git.snapshots import SnapshotLimits, SnapshotPair, freeze_snapshot


def seed_recovery_fixture(connection: Connection, artifact_root: Path) -> dict:
    base = freeze_snapshot("recovery-fixture", "a" * 40, (), ())
    target = freeze_snapshot("recovery-fixture", "b" * 40, (), ())
    pair = SnapshotPair(base, target, "owned-in-memory-fixture")
    identity = identity_from_snapshots(pair, run_id="recovery-run")
    absent = {
        name: StageResult(status="not_implemented", reason="fixture_not_implemented")
        for name in (
            "changes",
            "graph",
            "impact",
            "inventory",
            "retrieval",
            "evidence",
            "review_ordering",
        )
    }
    stages = AnalysisStages(snapshots=snapshots_result(pair), **absent)
    report = StageAnalysisReport(
        schema_version="2.0.0",
        report_id="recovery-report",
        data_kind="demo",
        identity=identity,
        analysis_status=aggregate_status(stages),
        stages=stages,
    )
    raw = report.model_dump_json(indent=2).encode() + b"\n"
    artifact = ReportArtifact(
        "recovery-file", "reports/recovery.json", hashlib.sha256(raw).hexdigest(), len(raw)
    )
    configuration = RunConfiguration(
        None, SnapshotLimits(), 256000, (("snapshots", "git-blobs/1"),)
    )
    write = prepare_run_report(
        report=report,
        configuration=configuration,
        snapshot_manifests=(base.manifest, target.manifest),
        artifact=artifact,
        published_report_bytes=raw,
    )
    file = artifact_root / artifact.storage_key
    file.parent.mkdir(parents=True, exist_ok=False)
    with file.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    connection.execute(
        repositories.insert().values(repository_id=identity.repository_id, source_kind="local")
    )
    connection.execute(
        snapshots.insert(),
        [
            {
                "repository_id": s.repository_id,
                "commit_sha": s.commit_sha,
                "snapshot_id": s.snapshot_id,
                "manifest_version": s.manifest_version,
                "materializer_version": s.materializer_version,
            }
            for s in write.snapshots
        ],
    )
    connection.execute(
        analysis_runs.insert().values(
            repository_id=identity.repository_id,
            run_id=identity.run_id,
            base_sha=identity.base.commit,
            target_sha=identity.target.commit,
            base_snapshot_id=identity.base.snapshot_id,
            target_snapshot_id=identity.target.snapshot_id,
            comparison_mode=identity.comparison_mode,
            data_kind=write.data_kind,
            configuration=json.loads(write.configuration_json),
            configuration_sha256=write.configuration_sha256,
        )
    )
    connection.execute(
        artifacts.insert().values(
            repository_id=identity.repository_id,
            run_id=identity.run_id,
            artifact_id=artifact.artifact_id,
            storage_key=artifact.storage_key,
            kind="report_json",
            sha256=artifact.sha256,
            size_bytes=artifact.size_bytes,
            media_type="application/json",
            schema_version="2.0.0",
            access_class="repository",
        )
    )
    connection.execute(
        run_reports.insert().values(
            repository_id=identity.repository_id,
            run_id=identity.run_id,
            report_id=write.report_id,
            artifact_id=artifact.artifact_id,
            schema_version="2.0.0",
            analysis_status=write.analysis_status,
            stage_summary=json.loads(write.stage_summary_json),
            analysis_duration_seconds=write.analysis_duration_seconds,
            llm_cost_usd=write.llm_cost_usd,
        )
    )
    return {"storage_key": artifact.storage_key, "sha256": artifact.sha256, "size_bytes": len(raw)}

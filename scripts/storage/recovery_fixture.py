"""Quiescent, task-owned report/file fixture for the backup/restore drill.

Fixture publication/provisioning is explicit; metadata uses the actual bound SQL adapter.
"""

import hashlib
import os
from pathlib import Path

from sqlalchemy import Connection

from smartregression.adapters.storage.inventory_store import BoundInventoryStore
from smartregression.adapters.storage.run_store import BoundRunReportStore
from smartregression.adapters.storage.schema import repositories
from smartregression.application.analysis import aggregate_status
from smartregression.application.inventory_store import InventoryConfiguration, prepare_inventory
from smartregression.application.run_store import (
    ReportArtifact,
    RunConfiguration,
    prepare_run_report,
)
from smartregression.application.stage_conversion import identity_from_snapshots, snapshots_result
from smartregression.contracts.stages import (
    AnalysisStages,
    InventoryPayload,
    StageAnalysisReport,
    StageResult,
)
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
    # Task-owned demo rows for recovery only; these IDs/image token are fixture
    # data, not claimed observations of a candidate or an executed collection.
    stages = stages.model_copy(
        update={
            "inventory": StageResult[InventoryPayload](
                status="completed",
                data=InventoryPayload(
                    snapshot=identity.target,
                    framework="pytest",
                    completeness="complete",
                    test_ids=[" test[đ] ", "test[é]", "test[e\u0301]", "test_" + "x" * 9000],
                ),
            )
        }
    )
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
    BoundRunReportStore(connection).save(write)
    BoundInventoryStore(connection).save(
        prepare_inventory(
            identity=identity,
            inventory_id="recovery-inventory",
            stage=stages.inventory,
            configuration=InventoryConfiguration(
                "recovery-fixture/1",
                "owned-recovery-fixture",
                "sha256:" + "0" * 64,
                "1" * 64,
                "2" * 64,
                "3" * 64,
            ),
        )
    )
    return {"storage_key": artifact.storage_key, "sha256": artifact.sha256, "size_bytes": len(raw)}

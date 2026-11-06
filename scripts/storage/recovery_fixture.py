"""Quiescent, task-owned report/file fixture for the backup/restore drill.

Fixture publication/provisioning is explicit; metadata uses the actual bound SQL adapter.
"""

import hashlib
import os
from pathlib import Path

from sqlalchemy import Connection

from smartregression.adapters.storage.evidence_store import BoundEvidenceStore
from smartregression.adapters.storage.index_artifacts import IndexArtifactFiles
from smartregression.adapters.storage.index_store import BoundIndexStore
from smartregression.adapters.storage.inventory_store import BoundInventoryStore
from smartregression.adapters.storage.run_store import BoundRunReportStore
from smartregression.adapters.storage.schema import repositories
from smartregression.application.analysis import aggregate_status
from smartregression.application.index_store import (
    IndexConfiguration,
    prepare_index_publication,
    record_value,
)
from smartregression.application.inventory_store import InventoryConfiguration, prepare_inventory
from smartregression.application.run_store import (
    ReportArtifact,
    RunConfiguration,
    prepare_run_report,
)
from smartregression.application.stage_conversion import identity_from_snapshots, snapshots_result
from smartregression.contracts.stages import (
    AnalysisStages,
    ChangePayload,
    EvidenceBundle,
    EvidencePayload,
    GraphPayload,
    ImpactPayload,
    InventoryPayload,
    StageAnalysisReport,
    StageResult,
)
from smartregression.core.git.snapshots import (
    SnapshotLimits,
    SnapshotPair,
    TreeEntry,
    freeze_snapshot,
)
from smartregression.core.retrieval.index_manifest import ChunkInput, build_index_manifest


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
    bundle = EvidenceBundle(
        identity=identity,
        changes=ChangePayload(components=[], files=[]),
        graph=GraphPayload(snapshot=identity.target, nodes=[], edges=[], unresolved=[]),
        impact=ImpactPayload(snapshot=identity.target, candidates=[], paths=[]),
        evidence=EvidencePayload(items=[]),
    )
    stages = stages.model_copy(
        update={
            name: StageResult(status="completed", data=getattr(bundle, name))
            for name in ("changes", "graph", "impact", "evidence")
        }
    )
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
    BoundEvidenceStore(connection).save(bundle)
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
    # Synthetic fixed recovery bytes, not a candidate/indexer acceptance claim.
    index_content = b"value = 1\r\n"
    blob = hashlib.sha1(
        b"blob " + str(len(index_content)).encode() + b"\0" + index_content
    ).hexdigest()
    index_snapshot = freeze_snapshot(
        "recovery-fixture",
        "c" * 40,
        (TreeEntry("src/recovery.py", "100644", blob, len(index_content)),),
        (index_content,),
    )
    index_config = IndexConfiguration(*("recovery-fixture/1",) * 6)
    index_manifest = build_index_manifest(
        index_snapshot,
        [ChunkInput("src/recovery.py", 1, 1, index_content)],
        index_version="recovery-fixture/1",
        configuration_id=index_config.digest,
    )
    index_publication = prepare_index_publication(
        index_snapshot,
        index_manifest,
        index_config,
        expected_chunks=1,
    )
    index_source = artifact_root.parent / "recovery-index-source"
    index_source.mkdir()
    index_files = IndexArtifactFiles(artifact_root, source_repository=index_source)
    index_store = BoundIndexStore(connection)
    index_store.begin(index_publication.record, "a" * 32)
    index_files.publish(index_publication)
    index_store.finish(index_publication.record, "a" * 32)
    return {
        "storage_key": artifact.storage_key,
        "sha256": artifact.sha256,
        "size_bytes": len(raw),
        "evidence_identity": identity.model_dump(mode="json"),
        "index_record": record_value(index_publication.record),
    }

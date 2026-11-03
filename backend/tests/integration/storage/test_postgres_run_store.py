import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
from uuid import uuid4

import pytest
import sqlalchemy as sa

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.adapters.storage.run_store import BoundRunReportStore, PostgresRunReportStore
from smartregression.adapters.storage.schema import (
    analysis_runs,
    artifacts,
    repositories,
    run_reports,
    snapshots,
)
from smartregression.application.persistence import persist_report
from smartregression.application.run_store import (
    ReportArtifact,
    RunConfiguration,
    RunConflict,
    RunMetadataError,
    RunStorageError,
    prepare_run_report,
)
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.git.snapshots import SnapshotLimits, SnapshotManifest


def arguments(data):
    repo = "store-fixture-" + uuid4().hex

    def scope(value):
        if isinstance(value, dict):
            return {
                key: repo if key == "repository_id" else scope(item) for key, item in value.items()
            }
        return [scope(item) for item in value] if isinstance(value, list) else value

    report = StageAnalysisReport.model_validate(scope(data))
    raw = report.model_dump_json(indent=2).encode() + b"\n"
    return dict(
        report=report,
        configuration=RunConfiguration(None, SnapshotLimits(), 256000, (("graph", None),)),
        snapshot_manifests=tuple(
            SnapshotManifest(
                s.repository_id,
                s.commit,
                (),
                s.snapshot_id,
                "snapshot/fixture",
                "materializer/fixture",
            )
            for s in (report.identity.base, report.identity.target)
            if s.snapshot_id
        ),
        artifact=ReportArtifact(
            "file-1", "reports/" + uuid4().hex + ".json", hashlib.sha256(raw).hexdigest(), len(raw)
        ),
        published_report_bytes=raw,
    )


def provision(engine, write):
    with engine.begin() as connection:
        connection.execute(
            repositories.insert().values(
                repository_id=write.identity.repository_id, source_kind="local"
            )
        )


def counts(engine, repository_id):
    with engine.connect() as connection:
        return [
            connection.scalar(
                sa.select(sa.func.count())
                .select_from(table)
                .where(table.c.repository_id == repository_id)
            )
            for table in (snapshots, analysis_runs, artifacts, run_reports)
        ]


def test_adapter_roundtrip_retry_keeps_exact_metadata_and_one_copy(migrated, stage_artifacts):
    owner, runtime, _ = migrated
    write = prepare_run_report(**arguments(stage_artifacts))
    provision(owner, write)
    store = PostgresRunReportStore(runtime)
    store.save(write)
    store.save(write)
    assert counts(owner, write.identity.repository_id) == [len(write.snapshots), 1, 1, 1]
    with owner.connect() as connection:
        row = (
            connection.execute(
                sa.select(run_reports).where(
                    run_reports.c.repository_id == write.identity.repository_id
                )
            )
            .mappings()
            .one()
        )
        assert row["stage_summary"] == json.loads(write.stage_summary_json)
        assert row["analysis_status"] == write.analysis_status
        assert row["llm_cost_usd"] is None
        config = connection.execute(
            sa.select(analysis_runs.c.configuration_sha256).where(
                analysis_runs.c.repository_id == write.identity.repository_id
            )
        ).scalar_one()
        assert config == write.configuration_sha256


@pytest.mark.parametrize(
    "change", ["config", "snapshot_version", "artifact", "summary", "key_alias"]
)
def test_immutable_mismatch_conflicts_without_partial_writes(migrated, stage_artifacts, change):
    owner, runtime, _ = migrated
    args = arguments(stage_artifacts)
    write = prepare_run_report(**args)
    provision(owner, write)
    store = PostgresRunReportStore(runtime)
    store.save(write)
    if change == "config":
        changed = prepare_run_report(
            **{**args, "configuration": replace(args["configuration"], application_version="2")}
        )
    elif change == "snapshot_version":
        changed = replace(
            write,
            snapshots=tuple(
                replace(s, materializer_version="different/1") for s in write.snapshots
            ),
        )
    elif change == "artifact":
        changed = replace(write, artifact=replace(write.artifact, sha256="f" * 64))
    elif change == "key_alias":
        changed = replace(write, artifact=replace(write.artifact, artifact_id="file-2"))
    else:
        changed = replace(write, analysis_duration_seconds=987.0)
    with pytest.raises(RunConflict):
        store.save(changed)
    assert counts(owner, write.identity.repository_id) == [len(write.snapshots), 1, 1, 1]


def test_missing_authorized_repository_is_not_registered_from_report(migrated, stage_artifacts):
    _, runtime, _ = migrated
    write = prepare_run_report(**arguments(stage_artifacts))
    with pytest.raises(RunStorageError):
        PostgresRunReportStore(runtime).save(write)
    assert counts(runtime, write.identity.repository_id) == [0, 0, 0, 0]


def test_real_adapter_rolls_back_after_late_write_failure(migrated, stage_artifacts):
    owner, runtime, _ = migrated
    write = prepare_run_report(**arguments(stage_artifacts))
    provision(owner, write)

    def fail_report(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO smartregression.run_reports"):
            raise RuntimeError("injected late failure")

    sa.event.listen(runtime, "before_cursor_execute", fail_report)
    try:
        with pytest.raises(RuntimeError, match="injected late failure"):
            PostgresRunReportStore(runtime).save(write)
    finally:
        sa.event.remove(runtime, "before_cursor_execute", fail_report)
    assert counts(owner, write.identity.repository_id) == [0, 0, 0, 0]


@pytest.mark.parametrize("same", [True, False])
def test_concurrent_adapter_saves_are_noop_or_conflict(migrated, stage_artifacts, same):
    owner, runtime, _ = migrated
    write = prepare_run_report(**arguments(stage_artifacts))
    provision(owner, write)
    other = write if same else replace(write, analysis_duration_seconds=987.0)
    barrier = Barrier(2)

    def save(value):
        barrier.wait(timeout=5)
        try:
            PostgresRunReportStore(runtime).save(value)
            return "saved"
        except RunConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(save, value) for value in (write, other)]
        assert sorted(f.result(timeout=15) for f in futures) == (
            ["saved", "saved"] if same else ["conflict", "saved"]
        )
    assert counts(owner, write.identity.repository_id) == [len(write.snapshots), 1, 1, 1]


def test_bound_adapter_leaves_transaction_to_owner(migrated, stage_artifacts):
    owner, runtime, _ = migrated
    write = prepare_run_report(**arguments(stage_artifacts))
    provision(owner, write)
    with (
        pytest.raises(RuntimeError, match="outer rollback"),
        database_transaction(runtime) as connection,
    ):
        BoundRunReportStore(connection).save(write)
        assert connection.in_transaction()
        raise RuntimeError("outer rollback")
    assert counts(owner, write.identity.repository_id) == [0, 0, 0, 0]


def test_invalid_metadata_rejected_without_connection(migrated, stage_artifacts):
    _, runtime, _ = migrated
    write = prepare_run_report(**arguments(stage_artifacts))
    with pytest.raises(RunMetadataError):
        PostgresRunReportStore(runtime).save(replace(write, report_id="bad\0value"))


def test_file_and_db_publication_roundtrip_uses_actual_adapter(migrated, stage_artifacts, tmp_path):
    owner, runtime, _ = migrated
    args = arguments(stage_artifacts)
    initial = prepare_run_report(**args)
    provision(owner, initial)
    source, root = tmp_path / "source", tmp_path / "reports"
    source.mkdir()
    root.mkdir()
    files = ReportFiles(root, source_repository=source)
    kwargs = {key: args[key] for key in ("report", "configuration", "snapshot_manifests")}
    for _ in range(2):
        write = persist_report(
            files,
            PostgresRunReportStore(runtime),
            artifact_id="file-1",
            storage_key="reports/published.json",
            **kwargs,
        )
    assert (
        files.read(
            write.artifact, expected_identity=write.identity, expected_report_id=write.report_id
        )
        == args["report"]
    )
    assert counts(owner, write.identity.repository_id) == [len(write.snapshots), 1, 1, 1]


def test_ambiguous_ack_after_real_commit_preserves_file_and_exact_retry(
    migrated, stage_artifacts, tmp_path
):
    owner, runtime, _ = migrated
    args = arguments(stage_artifacts)
    initial = prepare_run_report(**args)
    provision(owner, initial)
    source, root = tmp_path / "source", tmp_path / "artifacts"
    source.mkdir()
    root.mkdir()
    files = ReportFiles(root, source_repository=source)
    actual = PostgresRunReportStore(runtime)

    class LostAck:
        def save(self, write):
            actual.save(write)
            raise RunStorageError()

    kwargs = {key: args[key] for key in ("report", "configuration", "snapshot_manifests")}
    with pytest.raises(RunStorageError):
        persist_report(
            files, LostAck(), artifact_id="file-1", storage_key="reports/ack.json", **kwargs
        )
    assert (root / "reports/ack.json").exists()
    assert counts(owner, initial.identity.repository_id) == [len(initial.snapshots), 1, 1, 1]
    persist_report(files, actual, artifact_id="file-1", storage_key="reports/ack.json", **kwargs)
    assert counts(owner, initial.identity.repository_id) == [len(initial.snapshots), 1, 1, 1]


def test_actual_database_authentication_failure_has_safe_error(storage_context, stage_artifacts):
    from sqlalchemy.engine import URL

    from smartregression.adapters.storage.config import DatabaseSettings
    from smartregression.adapters.storage.connection import database_engine

    settings = DatabaseSettings(
        URL.create(
            "postgresql+psycopg",
            username="smartregression_runtime",
            password="synthetic-wrong-password",
            host="127.0.0.1",
            port=storage_context["port"],
            database="smartregression_kh_test",
            query={"sslmode": "disable"},
        ),
        allow_loopback_test=True,
    )
    write = prepare_run_report(**arguments(stage_artifacts))
    with pytest.raises(RunStorageError) as error, database_engine(settings) as engine:
        PostgresRunReportStore(engine).save(write)
    assert str(error.value) == "run_storage_failed"

"""Interleave actual PostgreSQL writers; events control order, not fake storage."""

import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event, current_thread
from uuid import uuid4

import pytest
import sqlalchemy as sa
from test_postgres_run_store import arguments, provision

from smartregression.adapters.storage.analysis_store import PostgresAnalysisStore
from smartregression.adapters.storage.evidence_store import (
    BoundEvidenceStore,
    PostgresEvidenceStore,
)
from smartregression.adapters.storage.run_store import PostgresRunReportStore
from smartregression.adapters.storage.schema import run_reports, run_stage_payloads
from smartregression.application.evidence_store import EvidenceConflict, EvidenceStorageError
from smartregression.application.persistence import bundle_from_report
from smartregression.application.run_store import (
    ReportArtifact,
    RunStorageError,
    prepare_run_report,
)
from smartregression.contracts.stages import StageAnalysisReport, StageResult


@pytest.mark.parametrize("standalone", [False, True])
@pytest.mark.parametrize("same", [False, True])
def test_interleaved_report_and_bundle_preserve_overlap(
    migrated, stage_artifacts, monkeypatch, standalone, same
):
    owner, runtime, _ = migrated
    args = arguments(stage_artifacts)
    complete = args["report"]

    def write(report):
        raw = report.model_dump_json(indent=2).encode() + b"\n"
        return prepare_run_report(
            **{
                **args,
                "report": report,
                "published_report_bytes": raw,
                "artifact": ReportArtifact(
                    report.report_id,
                    "reports/" + uuid4().hex + ".json",
                    hashlib.sha256(raw).hexdigest(),
                    len(raw),
                ),
            }
        )

    provision(owner, write(complete))
    # The standalone port requires an existing run. This seed has no overlapping
    # payload; it grants no permission to replace a later report's active graph.
    seed = complete.model_copy(
        update={
            "report_id": "seed",
            "analysis_status": "not_run",
            "stages": complete.stages.model_copy(
                update={
                    name: StageResult(status="not_run", reason="fixture_pending")
                    for name in type(complete.stages).model_fields
                }
            ),
        }
    )
    PostgresRunReportStore(runtime).save(write(seed))
    partial = complete.model_copy(
        update={
            "report_id": "report-only",
            "stages": complete.stages.model_copy(
                update={
                    "graph": complete.stages.graph
                    if same
                    else complete.stages.graph.model_copy(
                        update={"data": complete.stages.graph.data.model_copy(update={"edges": []})}
                    ),
                    **{
                        name: StageResult(status="not_run", reason="fixture_pending")
                        for name in ("impact", "evidence", "review_ordering")
                    },
                }
            ),
        }
    )
    partial = StageAnalysisReport.model_validate_json(partial.model_dump_json())
    first_read, release, second_done = Event(), Event(), Event()
    load = BoundEvidenceStore.load
    first_name = []

    def pause_after_read(self, identity):
        result = load(self, identity)
        if current_thread().name in first_name and not first_read.is_set():
            assert result is None
            first_read.set()
            assert release.wait(10), "Controller did not release the first writer"
        return result

    monkeypatch.setattr(BoundEvidenceStore, "load", pause_after_read)

    def first():
        first_name.append(current_thread().name)
        try:
            PostgresAnalysisStore(runtime, partial).save(write(partial))
            return "saved"
        except EvidenceConflict:
            return "conflict"

    def second():
        try:
            if standalone:
                PostgresEvidenceStore(runtime).save(bundle_from_report(complete))
            else:
                PostgresAnalysisStore(runtime, complete).save(write(complete))
            return "saved"
        except EvidenceConflict:
            return "conflict"
        finally:
            second_done.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(first)
        try:
            assert first_read.wait(5), "First writer never reached its overlap read"
            b = pool.submit(second)
            # Accept either the original race's committed writer or a real DB
            # lock wait. Do not force the fixed writer to exceed its lock budget.
            deadline = time.monotonic() + 5
            while not second_done.is_set():
                with owner.connect() as connection:
                    blocked = connection.scalar(
                        sa.text(
                            "SELECT EXISTS (SELECT 1 FROM pg_locks "
                            "WHERE locktype IN ('advisory', 'transactionid') AND NOT granted)"
                        )
                    )
                if blocked:
                    break
                assert time.monotonic() < deadline, "Second writer neither finished nor waited"
                second_done.wait(0.02)
        finally:
            release.set()
        first_result, second_result = a.result(timeout=10), b.result(timeout=10)
        outcomes = sorted([first_result, second_result])
    assert outcomes == (["saved", "saved"] if same else ["conflict", "saved"])
    stored = PostgresEvidenceStore(runtime).load(complete.identity)
    with runtime.connect() as connection:
        ids = set(
            connection.scalars(
                sa.select(run_reports.c.report_id).where(
                    run_reports.c.repository_id == complete.identity.repository_id
                )
            )
        )
    if same:
        assert stored == bundle_from_report(complete)
    else:
        # Either operation may claim the immutable payload first. The loser
        # rolls back all its own rows; contradictory payloads never coexist.
        if first_result == "saved":
            assert ids == {"seed", "report-only"}
            assert stored is None
        else:
            assert ids == ({"seed"} if standalone else {"seed", complete.report_id})
            assert stored == bundle_from_report(complete)


def test_legacy_report_claims_require_exact_replay(migrated, stage_artifacts):
    owner, runtime, _ = migrated
    args = arguments(stage_artifacts)
    report = args["report"]
    write = prepare_run_report(**args)
    provision(owner, write)
    PostgresRunReportStore(runtime).save(write)
    # Privileged fixture setup reproduces the pre-migration state. No runtime
    # delete or automatic trust/backfill of other reports is permitted.
    scope = [run_stage_payloads.c.repository_id == report.identity.repository_id]
    with owner.begin() as connection:
        connection.execute(run_stage_payloads.delete().where(*scope))
    bundle = bundle_from_report(report)
    with pytest.raises(EvidenceStorageError):
        PostgresEvidenceStore(runtime).save(bundle)
    assert PostgresEvidenceStore(runtime).load(report.identity) is None
    PostgresRunReportStore(runtime).save(write)
    PostgresEvidenceStore(runtime).save(bundle)
    assert PostgresEvidenceStore(runtime).load(report.identity) == bundle
    with runtime.connect() as connection:
        assert (
            connection.scalar(
                sa.select(sa.func.count()).select_from(run_stage_payloads).where(*scope)
            )
            == 4
        )


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE smartregression.run_stage_payloads SET payload_sha256=payload_sha256",
        "DELETE FROM smartregression.run_stage_payloads",
        "TRUNCATE smartregression.run_stage_payloads",
        "ALTER TABLE smartregression.run_stage_payloads ADD COLUMN forbidden text",
    ],
)
def test_runtime_cannot_mutate_payload_claims(migrated, statement):
    _, runtime, _ = migrated
    with pytest.raises(sa.exc.DBAPIError), runtime.begin() as connection:
        connection.execute(sa.text(statement))


def test_new_report_cannot_backfill_another_legacy_report(migrated, stage_artifacts):
    from dataclasses import replace

    owner, runtime, _ = migrated
    args = arguments(stage_artifacts)
    write = prepare_run_report(**args)
    provision(owner, write)
    PostgresRunReportStore(runtime).save(write)
    scope = [run_stage_payloads.c.repository_id == write.identity.repository_id]
    with owner.begin() as connection:
        connection.execute(run_stage_payloads.delete().where(*scope))
    # Even matching hashes supplied for a new report are not evidence of the
    # legacy report bytes. Its transaction must roll back its new catalog row.
    with pytest.raises(RunStorageError):
        PostgresRunReportStore(runtime).save(replace(write, report_id="new-report"))
    with runtime.connect() as connection:
        assert (
            connection.scalar(
                sa.select(sa.func.count()).select_from(run_stage_payloads).where(*scope)
            )
            == 0
        )
        assert set(
            connection.scalars(
                sa.select(run_reports.c.report_id).where(
                    run_reports.c.repository_id == write.identity.repository_id
                )
            )
        ) == {write.report_id}


def test_concurrent_compatible_report_is_not_misclassified_as_legacy(migrated, stage_artifacts):
    owner, runtime, _ = migrated
    args = arguments(stage_artifacts)
    write = prepare_run_report(**args)
    provision(owner, write)
    seed = args["report"].model_copy(
        update={
            "report_id": "seed",
            "analysis_status": "not_run",
            "stages": args["report"].stages.model_copy(
                update={
                    name: StageResult(status="not_run", reason="fixture_pending")
                    for name in type(args["report"].stages).model_fields
                }
            ),
        }
    )

    def prepare(report):
        raw = report.model_dump_json(indent=2).encode() + b"\n"
        return prepare_run_report(
            **{
                **args,
                "report": report,
                "published_report_bytes": raw,
                "artifact": ReportArtifact(
                    report.report_id,
                    "reports/" + uuid4().hex + ".json",
                    hashlib.sha256(raw).hexdigest(),
                    len(raw),
                ),
            }
        )

    PostgresRunReportStore(runtime).save(prepare(seed))
    selected, release = Event(), Event()
    thread_name = []

    def pause(connection, cursor, statement, parameters, context, executemany):
        if (
            current_thread().name in thread_name
            and not selected.is_set()
            and statement.startswith("SELECT smartregression.run_stage_payloads.stage_name")
        ):
            selected.set()
            assert release.wait(10)

    def first():
        thread_name.append(current_thread().name)
        PostgresRunReportStore(runtime).save(write)

    other = prepare(args["report"].model_copy(update={"report_id": "same-payload-other-report"}))
    sa.event.listen(runtime, "after_cursor_execute", pause)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(first)
            try:
                assert selected.wait(5)
                # A's SELECT snapshot predates B's commit. B's report and claims
                # become visible together; A must not label this new row legacy.
                pool.submit(PostgresRunReportStore(runtime).save, other).result(timeout=5)
            finally:
                release.set()
            a.result(timeout=10)
    finally:
        sa.event.remove(runtime, "after_cursor_execute", pause)
    with runtime.connect() as connection:
        assert set(
            connection.scalars(
                sa.select(run_reports.c.report_id).where(
                    run_reports.c.repository_id == write.identity.repository_id
                )
            )
        ) == {"seed", write.report_id, other.report_id}

import hashlib
import socket
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError, IntegrityError
from test_postgres_run_store import arguments, provision

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.evidence_store import (
    BoundEvidenceStore,
    PostgresEvidenceStore,
)
from smartregression.adapters.storage.run_store import BoundRunReportStore, PostgresRunReportStore
from smartregression.adapters.storage.schema import evidence_bundles
from smartregression.application.evidence_store import (
    EVIDENCE_FORMAT,
    EvidenceConflict,
    EvidenceCorrupt,
    EvidenceFormatUnsupported,
    EvidenceStorageError,
    prepare_evidence,
)
from smartregression.application.run_store import RunStorageError, prepare_run_report
from smartregression.contracts.stages import EvidenceBundle, StageResult


@pytest.fixture
def saved_run(migrated, stage_artifacts):
    owner, runtime, _ = migrated
    report = arguments(stage_artifacts)
    data = report["report"]
    bundle = EvidenceBundle(
        identity=data.identity,
        **{
            name: getattr(data.stages, name).data
            for name in ("changes", "graph", "impact", "evidence")
        },
    )
    # Standalone codec tests start with identity/configuration only. A cataloged
    # active report already claims its payloads and cannot authorize different
    # excerpts/graphs; that cross-writer policy has separate integration tests.
    seed = data.model_copy(
        update={
            "analysis_status": "not_run",
            "stages": data.stages.model_copy(
                update={
                    name: StageResult(status="not_run", reason="fixture_pending")
                    for name in type(data.stages).model_fields
                }
            ),
        }
    )
    raw = seed.model_dump_json(indent=2).encode() + b"\n"
    from dataclasses import replace

    write = prepare_run_report(
        **{
            **report,
            "report": seed,
            "published_report_bytes": raw,
            "artifact": replace(
                report["artifact"], sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)
            ),
        }
    )
    provision(owner, write)
    PostgresRunReportStore(runtime).save(write)
    return owner, runtime, bundle


def row(engine, bundle):
    with engine.connect() as connection:
        return (
            connection.execute(
                sa.select(evidence_bundles).where(
                    evidence_bundles.c.repository_id == bundle.identity.repository_id
                )
            )
            .mappings()
            .one()
        )


def test_roundtrip_and_retry_preserve_exact_bytes_and_created_at(saved_run):
    owner, runtime, bundle = saved_run
    bundle.evidence.items[0] = bundle.evidence.items[0].model_copy(
        update={"excerpt": "x\u0000é e\u0301"}
    )
    store = PostgresEvidenceStore(runtime)
    assert store.load(bundle.identity) is None
    store.save(bundle)
    first = row(owner, bundle)
    store.save(bundle)
    assert row(owner, bundle) == first
    assert first["payload"] == prepare_evidence(bundle)
    assert store.load(bundle.identity) == bundle
    other = bundle.model_copy(
        update={
            "evidence": bundle.evidence.model_copy(
                update={
                    "items": [
                        item.model_copy(update={"excerpt": "different"})
                        for item in bundle.evidence.items
                    ]
                }
            )
        }
    )
    with pytest.raises(EvidenceConflict):
        store.save(other)
    assert row(owner, bundle) == first


@pytest.mark.parametrize("side", ["base", "target"])
def test_full_snapshot_identity_is_checked_on_write_and_read(saved_run, side):
    _, runtime, bundle = saved_run
    store = PostgresEvidenceStore(runtime)
    store.save(bundle)
    identity = bundle.identity.model_copy(
        update={side: getattr(bundle.identity, side).model_copy(update={"snapshot_id": "f" * 64})}
    )
    with pytest.raises(EvidenceConflict):
        store.load(identity)
    old_digest = getattr(bundle.identity, side).snapshot_id

    def replace_digest(value):
        if isinstance(value, dict):
            return {key: replace_digest(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace_digest(item) for item in value]
        return "f" * 64 if value == old_digest else value

    foreign = EvidenceBundle.model_validate(replace_digest(bundle.model_dump(mode="json")))
    with pytest.raises(EvidenceConflict):
        store.save(foreign)


def test_ambiguous_commit_never_replays_or_deletes(saved_run, monkeypatch):
    _, runtime, bundle = saved_run

    @contextmanager
    def lost_ack(engine):
        with database_transaction(engine) as connection:
            yield connection
        # Server committed; caller cannot distinguish this from a lost commit ack.
        raise RunStorageError()

    with monkeypatch.context() as patch:
        patch.setattr(
            "smartregression.adapters.storage.evidence_store.database_transaction", lost_ack
        )
        with pytest.raises(EvidenceStorageError, match="^evidence_storage_failed$"):
            PostgresEvidenceStore(runtime).save(bundle)
    store = PostgresEvidenceStore(runtime)
    assert store.load(bundle.identity) == bundle
    store.save(bundle)  # Caller-held exact data reconciles as no-op.


def test_bound_store_rejects_connection_without_transaction(saved_run):
    _, runtime, bundle = saved_run
    with runtime.connect() as connection, pytest.raises(EvidenceStorageError):
        BoundEvidenceStore(connection).save(bundle)


@pytest.mark.parametrize("same", [True, False])
def test_concurrent_saves_keep_one_winner(saved_run, same):
    owner, runtime, bundle = saved_run
    other = EvidenceBundle.model_validate_json(bundle.model_dump_json())
    if not same:
        other.evidence.items[0] = other.evidence.items[0].model_copy(update={"excerpt": "other"})
    gate = Barrier(2)

    def save(value):
        gate.wait(timeout=5)
        try:
            PostgresEvidenceStore(runtime).save(value)
            return "saved"
        except EvidenceConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(save, (bundle, other)))
    assert sorted(result) == (["saved", "saved"] if same else ["conflict", "saved"])
    assert row(owner, bundle)["payload"] in (prepare_evidence(bundle), prepare_evidence(other))


@pytest.mark.parametrize("kind", ["json", "digest", "format", "noncanonical"])
def test_corruption_is_explicit_and_never_not_found(saved_run, kind):
    owner, runtime, bundle = saved_run
    PostgresEvidenceStore(runtime).save(bundle)
    raw = b"{broken" if kind == "json" else bundle.model_dump_json(indent=2).encode()
    values = {"payload": raw, "payload_sha256": hashlib.sha256(raw).hexdigest()}
    error = EvidenceCorrupt
    if kind == "digest":
        values = {"payload_sha256": "f" * 64}
    if kind == "format":
        values, error = {"bundle_format": "future/2"}, EvidenceFormatUnsupported
    with owner.begin() as connection:
        connection.execute(
            evidence_bundles.update()
            .where(evidence_bundles.c.repository_id == bundle.identity.repository_id)
            .values(**values)
        )
    with pytest.raises(error):
        PostgresEvidenceStore(runtime).load(bundle.identity)


def test_bound_store_shares_transaction_and_rolls_back_all_new_rows(migrated, stage_artifacts):
    owner, runtime, _ = migrated
    args = arguments(stage_artifacts)
    write = prepare_run_report(**args)
    provision(owner, write)
    report = args["report"]
    bundle = EvidenceBundle(
        identity=report.identity,
        **{
            name: getattr(report.stages, name).data
            for name in ("changes", "graph", "impact", "evidence")
        },
    )
    with (
        pytest.raises(RuntimeError, match="after_bundle"),
        database_transaction(runtime) as connection,
    ):
        BoundRunReportStore(connection).save(write)
        BoundEvidenceStore(connection).save(bundle)
        assert BoundEvidenceStore(connection).load(bundle.identity) == bundle
        raise RuntimeError("after_bundle")
    assert PostgresEvidenceStore(runtime).load(bundle.identity) is None
    with pytest.raises(EvidenceStorageError):
        PostgresEvidenceStore(runtime).save(bundle)


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE smartregression.evidence_bundles SET payload=payload",
        "DELETE FROM smartregression.evidence_bundles",
        "TRUNCATE smartregression.evidence_bundles",
        "ALTER TABLE smartregression.evidence_bundles ADD COLUMN forbidden text",
        "DROP TABLE smartregression.evidence_bundles",
    ],
)
def test_runtime_cannot_mutate_or_drop_evidence(saved_run, statement):
    _, runtime, bundle = saved_run
    PostgresEvidenceStore(runtime).save(bundle)
    with pytest.raises(DBAPIError), runtime.begin() as connection:
        connection.execute(sa.text(statement))


def test_database_size_check_and_unavailable_connection(saved_run):
    owner, runtime, bundle = saved_run
    with pytest.raises(IntegrityError), owner.begin() as connection:
        connection.execute(
            evidence_bundles.insert().values(
                repository_id=bundle.identity.repository_id,
                run_id=bundle.identity.run_id,
                bundle_format=EVIDENCE_FORMAT,
                payload=b"x" * 2_097_153,
                payload_sha256="f" * 64,
            )
        )
    # Reserve our own loopback port without listening, so no other DB can be contacted.
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        unavailable = sa.create_engine(
            runtime.url.set(port=reserved.getsockname()[1]),
            connect_args={"connect_timeout": 1},
            hide_parameters=True,
        )
        try:
            with pytest.raises(EvidenceStorageError, match="^evidence_storage_failed$"):
                PostgresEvidenceStore(unavailable).load(bundle.identity)
        finally:
            unavailable.dispose()


def test_concurrent_insert_lock_timeout_is_explicit_and_does_not_replay(saved_run):
    _, runtime, bundle = saved_run

    def contender():
        with database_transaction(runtime) as connection:
            connection.execute(sa.text("SET LOCAL lock_timeout = '100ms'"))
            with pytest.raises(EvidenceStorageError, match="^evidence_storage_failed$"):
                BoundEvidenceStore(connection).save(bundle)
            # The failed statement aborted this transaction; exiting it must not
            # turn the blocked insert into a background retry.

    with database_transaction(runtime) as connection:
        BoundEvidenceStore(connection).save(bundle)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(contender).result(timeout=10)
    assert PostgresEvidenceStore(runtime).load(bundle.identity) == bundle

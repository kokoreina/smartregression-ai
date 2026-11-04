import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
import sqlalchemy as sa
from test_foundation import seed

from smartregression.adapters.storage.inventory_store import (
    BoundInventoryStore,
    PostgresInventoryStore,
    _header,
)
from smartregression.adapters.storage.schema import (
    analysis_runs,
    repositories,
    snapshots,
    test_cases,
    test_inventories,
)
from smartregression.application.inventory_store import (
    InventoryConfiguration,
    InventoryConflict,
    InventoryWrite,
    UnsupportedTestId,
    prepare_inventory,
    require_complete_inventory_ids,
    validate_inventory_write,
)
from smartregression.application.inventory_store import (
    test_id_digest as native_digest,
)
from smartregression.application.run_store import RunStorageError
from smartregression.contracts.stages import InventoryPayload, RunIdentity, StageResult


def write_for(owner, ids=(" test[đ] ",), status="completed", missing_snapshot=False):
    with owner.begin() as connection:
        repo, run = seed(connection, repository="inventory-" + uuid4().hex)
        if missing_snapshot:
            connection.execute(
                analysis_runs.update()
                .where(analysis_runs.c.repository_id == repo)
                .values(target_snapshot_id=None)
            )
    identity = RunIdentity.model_validate(
        dict(
            repository_id=repo,
            run_id=run["run_id"],
            comparison_mode="direct_two_tree",
            base=dict(repository_id=repo, commit="a" * 40, snapshot_id="c" * 64),
            target=dict(
                repository_id=repo,
                commit="b" * 40,
                snapshot_id=None if missing_snapshot else "d" * 64,
            ),
        )
    )
    active = status in {"partial", "completed"}
    stage = StageResult[InventoryPayload](
        status=status,
        data=InventoryPayload(
            snapshot=identity.target,
            framework="pytest",
            test_ids=list(ids),
            completeness="partial" if status == "partial" else "complete",
        )
        if active
        else None,
        reason="not_scheduled" if status in {"not_run", "not_implemented"} else None,
        error_code="collection_failed" if status == "failed" else None,
        limitations=[{"code": "collection_errors"}] if status == "partial" else [],
    )
    return prepare_inventory(
        identity=identity,
        inventory_id="inventory-1",
        stage=stage,
        configuration=InventoryConfiguration(
            "candidate-inventory/1", "sqlparse", "sha256:" + "e" * 64, "f" * 64, "a" * 64, "b" * 64
        ),
        exit_code=2 if status in {"partial", "failed"} else None,
        duration_seconds=1.25,
    )


def load(store, write):
    return store.load(write.identity, write.inventory_id, write.configuration_sha256)


@pytest.mark.parametrize(
    "status,ids",
    [
        ("not_implemented", ()),
        ("not_run", ()),
        ("failed", ()),
        ("partial", ()),
        ("partial", ("test[one]",)),
        ("completed", ()),
        ("completed", (" ", " test[đ] ", "test[é]", "test[e\u0301]", "x" * 12000)),
    ],
)
def test_roundtrip_contract_database_consumer_retry(migrated, status, ids):
    owner, runtime, _ = migrated
    write = write_for(owner, ids, status)
    store = PostgresInventoryStore(runtime)
    store.save(write)
    store.save(write)
    assert load(store, write) == write
    if write.stage.data:
        assert load(store, write).stage.data.test_ids == list(ids)
    with owner.connect() as connection:
        row = (
            connection.execute(
                sa.select(test_inventories).where(
                    test_inventories.c.repository_id == write.identity.repository_id
                )
            )
            .mappings()
            .one()
        )
        assert row["test_count"] == (len(ids) if status in {"completed", "partial"} else None)


@pytest.mark.parametrize("status", ["not_implemented", "not_run", "failed"])
def test_pre_acquisition_states_do_not_invent_snapshot(migrated, status):
    owner, runtime, _ = migrated
    write = write_for(owner, (), status, missing_snapshot=True)
    store = PostgresInventoryStore(runtime)
    store.save(write)
    assert load(store, write).identity.target.snapshot_id is None


def test_changed_payload_or_second_inventory_for_same_run_conflicts(migrated):
    owner, runtime, _ = migrated
    write = write_for(owner)
    store = PostgresInventoryStore(runtime)
    store.save(write)
    for changed in [replace(write, duration_seconds=2), replace(write, inventory_id="second")]:
        with pytest.raises(InventoryConflict):
            store.save(changed)
    assert load(store, write) == write


def test_wrong_target_and_configuration_are_rejected_on_save_and_load(migrated):
    owner, runtime, _ = migrated
    write = write_for(owner, status="not_run")
    store = PostgresInventoryStore(runtime)
    store.save(write)
    other = write.identity.model_dump(mode="json")
    other["target"]["snapshot_id"] = "e" * 64
    other = RunIdentity.model_validate(other)
    with pytest.raises(InventoryConflict):
        store.load(other, write.inventory_id, write.configuration_sha256)
    with pytest.raises(InventoryConflict):
        store.save(
            replace(
                write,
                identity_json=json.dumps(
                    other.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
                )
                + "\n",
            )
        )
    with pytest.raises(InventoryConflict):
        store.load(write.identity, write.inventory_id, "0" * 64)


def test_simulated_digest_collision_rejects_exact_different_ids_before_write(migrated, monkeypatch):
    owner, runtime, _ = migrated
    write = write_for(owner, ("test_one", "test_two"))
    monkeypatch.setattr(
        "smartregression.adapters.storage.inventory_store.test_id_digest", lambda _: "0" * 64
    )
    with pytest.raises(InventoryConflict):
        PostgresInventoryStore(runtime).save(write)
    assert load(PostgresInventoryStore(runtime), write) is None


def test_late_sql_error_rolls_back_header_and_cases(migrated):
    owner, runtime, _ = migrated
    write = write_for(owner)

    def fail(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO smartregression.test_cases"):
            raise sa.exc.OperationalError("owned late failure", None, Exception())

    sa.event.listen(runtime, "before_cursor_execute", fail)
    try:
        with pytest.raises(RunStorageError):
            PostgresInventoryStore(runtime).save(write)
    finally:
        sa.event.remove(runtime, "before_cursor_execute", fail)
    assert load(PostgresInventoryStore(runtime), write) is None


@pytest.mark.parametrize("different", [False, True])
def test_two_connections_arbitrate_same_inventory(migrated, different):
    owner, runtime, _ = migrated
    write = write_for(owner)
    barrier = Barrier(2)

    def attempt(value):
        barrier.wait(timeout=10)
        try:
            PostgresInventoryStore(runtime).save(value)
            return "ok"
        except InventoryConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        values = [write, replace(write, duration_seconds=9) if different else write]
        results = sorted(pool.map(attempt, values))
    assert results == (["conflict", "ok"] if different else ["ok", "ok"])


@pytest.mark.parametrize(
    "mutation",
    [
        {"stage_status": "failed", "test_count": 0},
        {"test_count": None},
        {"target_snapshot_id": None},
        {"target_sha": "a" * 40, "target_snapshot_id": "c" * 64},
        {"configuration": []},
        {"completeness": None},
    ],
)
def test_database_rejects_invalid_state_scope_and_presence(migrated, mutation):
    owner, _, _ = migrated
    write = write_for(owner, ())
    with pytest.raises(sa.exc.IntegrityError), owner.begin() as connection:
        connection.execute(test_inventories.insert().values(**(_header(write) | mutation)))


def test_deferred_count_constraint_prevents_incomplete_commit(migrated):
    owner, _, _ = migrated
    write = write_for(owner)
    with pytest.raises(sa.exc.IntegrityError), owner.begin() as connection:
        connection.execute(test_inventories.insert().values(**_header(write)))


def test_wrong_digest_or_ordinal_rejected_by_database(migrated):
    owner, _, _ = migrated
    for digest, ordinal in [("0" * 64, 0), (native_digest("test_one"), 5)]:
        write = write_for(owner, ("test_one",))
        with pytest.raises(sa.exc.IntegrityError), owner.begin() as connection:
            connection.execute(test_inventories.insert().values(**_header(write)))
            connection.execute(
                test_cases.insert().values(
                    repository_id=write.identity.repository_id,
                    run_id=write.identity.run_id,
                    inventory_id=write.inventory_id,
                    test_id_sha256=digest,
                    test_id="test_one",
                    ordinal=ordinal,
                )
            )


def test_null_id_has_safe_explicit_error_and_no_rows(migrated):
    owner, runtime, _ = migrated
    write = write_for(owner)
    from smartregression.application.inventory_store import validate_inventory_write

    payload = json.loads(write.stage_json)
    payload["data"]["test_ids"] = ["test\0id"]
    from smartregression.core.git.snapshots import canonical_json

    with pytest.raises(UnsupportedTestId, match="unsupported_test_id"):
        validate_inventory_write(replace(write, stage_json=canonical_json(payload).decode()))
    assert load(PostgresInventoryStore(runtime), write) is None


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE smartregression.test_inventories SET test_count=0",
        "DELETE FROM smartregression.test_cases",
        "CREATE TABLE smartregression.inventory_should_not_exist (id int)",
    ],
)
def test_runtime_cannot_mutate_history_or_schema(migrated, sql):
    _, runtime, _ = migrated
    with pytest.raises(sa.exc.DBAPIError), runtime.begin() as connection:
        connection.execute(sa.text(sql))


def test_bound_store_requires_transaction(migrated):
    owner, runtime, _ = migrated
    write = write_for(owner)
    with runtime.connect() as connection, pytest.raises(RunStorageError):
        BoundInventoryStore(connection).save(write)


@pytest.mark.parametrize("name", ["sqlparse", "tinydb"])
def test_actual_candidate_ids_roundtrip_in_postgresql(migrated, name):
    owner, runtime, _ = migrated
    raw = os.environ.get("SMARTREGRESSION_INVENTORY_CANDIDATES")
    if raw is None:
        pytest.skip("Run scripts/inventory/verify_complete.ps1 for real candidate -> DB checks")
    root = Path(__file__).resolve().parents[4]
    evidence_path = Path(raw)
    assert not any(
        p.is_symlink() or p.is_junction() for p in (evidence_path, *evidence_path.parents)
    )
    evidence_path = evidence_path.resolve(strict=True)
    assert evidence_path.is_relative_to(root / "var")
    evidence = json.loads(evidence_path.read_text())
    assert evidence["passed"] is True
    record = evidence["candidates"][name]
    assert (
        record["attempts"][0]["stage"]["data"]["test_ids"]
        == record["attempts"][1]["stage"]["data"]["test_ids"]
    )
    write = validate_inventory_write(
        InventoryWrite(
            **json.loads((evidence_path.parent / name / "inventory-write.json").read_text())
        )
    )
    assert write.configuration.image_id == evidence["image_id"]
    identity = write.identity
    with owner.begin() as connection:
        connection.execute(repositories.insert().values(repository_id=name, source_kind="github"))
        connection.execute(
            snapshots.insert().values(
                repository_id=name,
                commit_sha=identity.target.commit,
                snapshot_id=identity.target.snapshot_id,
                manifest_version="snapshot/1",
                materializer_version="git-blobs/1",
            )
        )
        config = {"inventory_configuration_sha256": write.configuration_sha256}
        from smartregression.core.git.snapshots import canonical_json

        connection.execute(
            analysis_runs.insert().values(
                repository_id=name,
                run_id=identity.run_id,
                base_sha=identity.base.commit,
                target_sha=identity.target.commit,
                base_snapshot_id=identity.base.snapshot_id,
                target_snapshot_id=identity.target.snapshot_id,
                comparison_mode="direct_two_tree",
                data_kind="real",
                configuration=config,
                configuration_sha256=hashlib.sha256(canonical_json(config)).hexdigest(),
            )
        )
    store = PostgresInventoryStore(runtime)
    store.save(write)
    store.save(write)
    loaded = load(store, write)
    assert loaded == write
    assert require_complete_inventory_ids(
        loaded, identity=identity, configuration_sha256=write.configuration_sha256
    ) == tuple(write.stage.data.test_ids)
    assert loaded.stage.data.test_ids == record["attempts"][0]["stage"]["data"]["test_ids"]

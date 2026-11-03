from dataclasses import replace

import pytest

from smartregression.core.execution.inventory import (
    InventoryIdentity,
    InventoryValidationError,
    finalize_discovery,
    require_inventory_ids,
)


@pytest.fixture
def identity():
    return InventoryIdentity(
        repository_id="owned-fixture",
        run_id="run-1",
        target_commit="a" * 40,
        snapshot_digest="b" * 64,
        configuration_digest="c" * 64,
    )


def observation(ids=(), *, exit_code=0, finished=True, errors=0):
    return {
        "ids": list(ids),
        "exit_code": exit_code,
        "collection_finished": finished,
        "collection_errors": errors,
    }


def finish(identity, payload=None, **kwargs):
    return finalize_discovery(
        expected=identity,
        observed=identity,
        payload=observation(["tests/test_a.py::test_one"]) if payload is None else payload,
        **kwargs,
    )


def test_complete_inventory_preserves_native_ids_and_identity(identity):
    ids = ["tests/test_a.py::TestA::test_x[a b/đ]", "custom collector item"]
    payload = observation(ids)
    result = finish(identity, payload)
    payload["ids"].clear()
    assert result.identity == identity
    assert result.status == "complete"
    assert result.reason is None
    assert result.observed_ids == tuple(ids)
    assert require_inventory_ids(result, expected=identity) == tuple(ids)


@pytest.mark.parametrize(
    ("payload", "status", "reason"),
    [
        (observation(exit_code=5), "empty", None),
        (observation(exit_code=2), "failed", "collection_failed"),
        (observation(["test_a"], exit_code=2, errors=1), "partial", "collection_failed"),
        (observation(["test_a"], errors=1), "partial", "collection_errors"),
        (observation(errors=1), "failed", "collection_errors"),
        (observation(["test_a"], finished=False), "partial", "collection_unfinished"),
        (observation(finished=False), "failed", "collection_unfinished"),
        (observation(), "failed", "inconsistent_exit_code"),
        (observation(["test_a"], exit_code=5), "failed", "inconsistent_exit_code"),
        (observation(["test_a"], exit_code=3), "partial", "collection_failed"),
    ],
)
def test_collection_state_matrix(identity, payload, status, reason):
    result = finish(identity, payload)
    assert (result.status, result.reason) == (status, reason)
    if status == "empty":
        assert require_inventory_ids(result, expected=identity) == ()
    else:
        with pytest.raises(InventoryValidationError, match="incomplete_inventory"):
            require_inventory_ids(result, expected=identity)


@pytest.mark.parametrize("termination", ["timeout", "output_limit", "infrastructure_error"])
@pytest.mark.parametrize("has_payload", [True, False])
def test_controller_failure_never_becomes_success(identity, termination, has_payload):
    result = finalize_discovery(
        expected=identity,
        observed=identity,
        payload=observation(["test_a"]) if has_payload else None,
        termination=termination,
    )
    assert result.status == ("timeout" if termination == "timeout" else "failed")
    assert result.reason == termination
    assert result.observed_ids == (("test_a",) if has_payload else ())
    with pytest.raises(InventoryValidationError, match="incomplete_inventory"):
        require_inventory_ids(result, expected=identity)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("repository_id", "other-repo"),
        ("run_id", "other-run"),
        ("target_commit", "d" * 40),
        ("snapshot_digest", "d" * 64),
        ("configuration_digest", "d" * 64),
    ],
)
def test_stale_or_foreign_identity_is_rejected(identity, field, value):
    other = replace(identity, **{field: value})
    with pytest.raises(InventoryValidationError, match="inventory_identity_mismatch"):
        finalize_discovery(expected=identity, observed=other, payload=observation())
    with pytest.raises(InventoryValidationError, match="inventory_identity_mismatch"):
        require_inventory_ids(finish(identity), expected=other)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {**observation(), "fault_labels": []},
        {**observation(), "exit_code": True},
        {**observation(), "exit_code": -1},
        {**observation(), "exit_code": 6},
        {**observation(), "collection_finished": 1},
        {**observation(), "collection_errors": -1},
        {**observation(), "collection_errors": True},
        {**observation(), "ids": "test_a"},
        {**observation(), "ids": [None]},
        observation([""]),
        observation(["   "]),
        observation(["test\nsecret"]),
        observation(["test\x1b[31m"]),
        observation(["test\ud800"]),
        observation(["test_a", "test_a"]),
        observation(["x" * 8193]),
        observation([str(i) for i in range(10001)]),
        observation([str(i) + "x" * 8000 for i in range(70)]),
    ],
)
def test_untrusted_payload_is_rejected_without_echoing_input(identity, payload):
    with pytest.raises(InventoryValidationError) as error:
        finish(identity, payload)
    assert str(error.value) in {
        "invalid_collection_payload",
        "duplicate_test_id",
        "inventory_limit",
    }
    assert "secret" not in str(error.value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("repository_id", ""),
        ("run_id", "\n"),
        ("target_commit", "main"),
        ("target_commit", "A" * 40),
        ("snapshot_digest", "b" * 40),
        ("configuration_digest", ""),
    ],
)
def test_identity_requires_explicit_frozen_references(identity, field, value):
    with pytest.raises(InventoryValidationError, match="invalid_inventory_identity"):
        replace(identity, **{field: value})


def test_sha256_git_repository_is_supported(identity):
    sha256 = replace(identity, target_commit="e" * 64)
    assert finish(sha256).identity.target_commit == "e" * 64


def test_missing_payload_is_failure_not_empty(identity):
    result = finalize_discovery(expected=identity, observed=identity, payload=None)
    assert (result.status, result.reason) == ("failed", "missing_collection_payload")


def test_unknown_controller_termination_is_rejected(identity):
    with pytest.raises(InventoryValidationError, match="invalid_termination"):
        finish(identity, termination="success")


def test_utf8_limit_is_bytes_and_native_whitespace_is_not_normalized(identity):
    with pytest.raises(InventoryValidationError, match="inventory_limit"):
        finish(identity, observation(["đ" * 4097]))
    ids = [" tests/test_a.py::test_x[ a ] ", "tests/test_a.py::test_x[ a ]"]
    assert require_inventory_ids(finish(identity, observation(ids)), expected=identity) == tuple(
        ids
    )


def test_invalid_identity_objects_and_termination_have_stable_errors(identity):
    with pytest.raises(InventoryValidationError, match="invalid_inventory_identity"):
        finalize_discovery(expected=None, observed=identity, payload=observation())
    with pytest.raises(InventoryValidationError, match="invalid_termination"):
        finish(identity, termination=[])

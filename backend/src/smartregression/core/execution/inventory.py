"""Internal discovery validation for tasks 2.08/2.09, not a stage/API contract.

No collection or dispatch happens here. A trusted isolated adapter must supply
identity and controller termination independently of untrusted worker output.
Canonical projection and persistence live in application/adapters.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

DiscoveryStatus = Literal["complete", "empty", "partial", "failed", "timeout"]
Termination = Literal["exited", "timeout", "output_limit", "infrastructure_error"]

# Bounded parser safeguards; the candidate transport also caps encoded output.
MAX_TESTS = 10_000
MAX_INVENTORY_BYTES = 512 * 1024


class InventoryValidationError(ValueError):
    """Stable reason only; never include source, node IDs or raw worker logs."""


def _valid_text(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not any(unicodedata.category(char) in {"Cc", "Cs"} for char in value)
    )


@dataclass(frozen=True)
class InventoryIdentity:
    repository_id: str
    run_id: str
    target_commit: str
    snapshot_digest: str
    configuration_digest: str

    def __post_init__(self) -> None:
        if (
            not all(_valid_text(v) and len(v) <= 512 for v in (self.repository_id, self.run_id))
            or not isinstance(self.target_commit, str)
            or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", self.target_commit)
            or not all(
                isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v)
                for v in (self.snapshot_digest, self.configuration_digest)
            )
        ):
            raise InventoryValidationError("invalid_inventory_identity")


@dataclass(frozen=True)
class DiscoveryResult:
    identity: InventoryIdentity
    observed_ids: tuple[str, ...]
    status: DiscoveryStatus
    reason: str | None
    exit_code: int | None
    collection_finished: bool
    collection_errors: int | None
    checkpoint_valid: bool = False


def _parse_payload(payload: object) -> tuple[tuple[str, ...], int, bool, int, bool]:
    required = {
        "ids",
        "exit_code",
        "collection_finished",
        "collection_errors",
    }
    if type(payload) is not dict or set(payload) not in (required, required | {"checkpoint_valid"}):
        raise InventoryValidationError("invalid_collection_payload")
    ids, code = payload["ids"], payload["exit_code"]
    finished, errors = payload["collection_finished"], payload["collection_errors"]
    checkpoint = payload.get("checkpoint_valid", False)
    if (
        type(ids) is not list
        or type(code) is not int
        or code not in range(6)
        or type(finished) is not bool
        or type(errors) is not int
        or errors < 0
        or type(checkpoint) is not bool
    ):
        raise InventoryValidationError("invalid_collection_payload")
    if len(ids) > MAX_TESTS:
        raise InventoryValidationError("inventory_limit")
    seen: set[str] = set()
    total = 0
    for test_id in ids:
        if (
            not isinstance(test_id, str)
            or not test_id
            or any(unicodedata.category(char) in {"Cc", "Cs"} for char in test_id)
        ):
            raise InventoryValidationError("invalid_collection_payload")
        size = len(test_id.encode("utf-8"))
        total += size
        if total > MAX_INVENTORY_BYTES:
            raise InventoryValidationError("inventory_limit")
        if test_id in seen:
            raise InventoryValidationError("duplicate_test_id")
        seen.add(test_id)
    return tuple(ids), code, finished, errors, checkpoint


def finalize_discovery(
    *,
    expected: InventoryIdentity,
    observed: InventoryIdentity,
    payload: object,
    termination: Termination = "exited",
) -> DiscoveryResult:
    """Freeze native IDs; incomplete IDs remain diagnostic and cannot be consumed.

    Successful empty requires pytest exit 5 plus a completed, error-free collection.
    Controller timeout/output/infra signals override otherwise successful payloads.
    Identity equality binds observations; it does not attest authorization/isolation.
    """
    if not isinstance(expected, InventoryIdentity) or not isinstance(observed, InventoryIdentity):
        raise InventoryValidationError("invalid_inventory_identity")
    if expected != observed:
        raise InventoryValidationError("inventory_identity_mismatch")
    if type(termination) is not str or termination not in {
        "exited",
        "timeout",
        "output_limit",
        "infrastructure_error",
    }:
        raise InventoryValidationError("invalid_termination")
    ids, code, finished, errors, checkpoint = (
        ((), None, False, None, False) if payload is None else _parse_payload(payload)
    )
    status: DiscoveryStatus
    reason: str | None
    if termination != "exited":
        status = "timeout" if termination == "timeout" else "failed"
        reason = termination
    elif payload is None:
        status, reason = "failed", "missing_collection_payload"
    elif code in {1, 3, 4}:
        status, reason = "failed", "collection_failed"
    elif code == 2:
        status, reason = ("partial" if ids or checkpoint else "failed"), "collection_failed"
    elif errors:
        status, reason = ("partial" if ids else "failed"), "collection_errors"
    elif not finished:
        status, reason = ("partial" if ids else "failed"), "collection_unfinished"
    elif (code == 0 and not ids) or (code == 5 and ids):
        status, reason = "failed", "inconsistent_exit_code"
    else:
        status, reason = ("complete" if ids else "empty"), None
    return DiscoveryResult(observed, ids, status, reason, code, finished, errors, checkpoint)


def require_inventory_ids(
    result: DiscoveryResult, *, expected: InventoryIdentity
) -> tuple[str, ...]:
    """Consumer guard; a complete empty inventory does not assert absence of risk."""
    if result.identity != expected:
        raise InventoryValidationError("inventory_identity_mismatch")
    if result.status not in {"complete", "empty"}:
        raise InventoryValidationError("incomplete_inventory")
    return result.observed_ids

"""Target discovery boundary and projection onto canonical v2 stage reports."""

import subprocess
from typing import Protocol

from smartregression.contracts.stages import (
    InventoryPayload,
    RunIdentity,
    StageIssue,
    StageResult,
)
from smartregression.core.execution.inventory import (
    DiscoveryResult,
    InventoryIdentity,
    InventoryValidationError,
    finalize_discovery,
)
from smartregression.core.git.snapshots import FrozenSnapshot, validate_frozen_snapshot

_SAFE_ERRORS = frozenset(
    {
        "inventory_identity_mismatch",
        "invalid_collection_payload",
        "duplicate_test_id",
        "inventory_limit",
        "snapshot_mismatch",
        "fixture_not_authorized",
        "unsupported_snapshot",
        "invalid_worker_result",
        "output_limit",
        "isolation_not_enforced",
        "collector_configuration_changed",
        "discovery_infrastructure_error",
        "candidate_not_authorized",
        "candidate_environment_mismatch",
    }
)


class InventoryCollector(Protocol):
    @property
    def configuration_digest(self) -> str: ...

    def collect(self, snapshot: FrozenSnapshot, *, identity: InventoryIdentity) -> DiscoveryResult:
        """Collect only inside an explicitly authorized isolated worker."""
        ...


def inventory_identity(identity: RunIdentity, configuration_digest: str) -> InventoryIdentity:
    return InventoryIdentity(
        identity.repository_id,
        identity.run_id,
        identity.target.commit,
        identity.target.snapshot_id,
        configuration_digest,
    )


def inventory_stage(
    result: DiscoveryResult, identity: RunIdentity
) -> StageResult[InventoryPayload]:
    expected = inventory_identity(identity, result.identity.configuration_digest)
    if result.identity != expected:
        raise InventoryValidationError("inventory_identity_mismatch")
    # Dataclasses are internal, but callers can still construct/replace them. Do
    # not let a relabelled partial result cross the canonical report boundary.
    termination = (
        result.reason
        if result.reason in {"timeout", "output_limit", "infrastructure_error"}
        else "exited"
    )
    payload = (
        None
        if result.exit_code is None
        else {
            "ids": list(result.observed_ids),
            "exit_code": result.exit_code,
            "collection_finished": result.collection_finished,
            "collection_errors": result.collection_errors,
            "checkpoint_valid": result.checkpoint_valid,
        }
    )
    checked = finalize_discovery(
        expected=expected, observed=result.identity, payload=payload, termination=termination
    )
    if checked != result:
        raise InventoryValidationError("invalid_discovery_result")
    if result.status in {"failed", "timeout"}:
        return StageResult(
            status="failed",
            error_code="discovery_timeout" if result.status == "timeout" else result.reason,
        )
    data = InventoryPayload(
        snapshot=identity.target,
        framework="pytest",
        test_ids=list(result.observed_ids),
        completeness="partial" if result.status == "partial" else "complete",
    )
    if data.test_ids != list(result.observed_ids):
        # Guard against deployment with an older v2 reader that still trims IDs.
        return StageResult(status="failed", error_code="native_test_id_normalization")
    return StageResult(
        status="partial" if result.status == "partial" else "completed",
        data=data,
        limitations=[StageIssue(code=result.reason)] if result.status == "partial" else [],
    )


def collect_inventory(
    snapshot: FrozenSnapshot, identity: RunIdentity, collector: InventoryCollector
) -> StageResult[InventoryPayload]:
    try:
        validate_frozen_snapshot(snapshot)
        manifest = snapshot.manifest
        if (manifest.repository_id, manifest.commit, manifest.snapshot_id) != (
            identity.repository_id,
            identity.target.commit,
            identity.target.snapshot_id,
        ):
            raise InventoryValidationError("inventory_identity_mismatch")
        expected = inventory_identity(identity, collector.configuration_digest)
        result = collector.collect(snapshot, identity=expected)
        if not isinstance(result, DiscoveryResult):
            raise InventoryValidationError("invalid_discovery_result")
        if result.identity != expected:
            raise InventoryValidationError("inventory_identity_mismatch")
        return inventory_stage(result, identity)
    except subprocess.TimeoutExpired:
        return StageResult(status="failed", error_code="discovery_timeout")
    except OSError:
        return StageResult(status="failed", error_code="discovery_infrastructure_error")
    except ValueError as exc:
        code = str(exc)
        if code == "invalid_discovery_result":
            return StageResult(status="failed", error_code=code)
        return StageResult(
            status="failed",
            error_code=code if code in _SAFE_ERRORS else "inventory_discovery_failed",
        )

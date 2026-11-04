"""Frozen inventory persistence values and port; no engine or collection side effects."""

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from typing import Protocol

from pydantic import ValidationError

from smartregression.application.run_store import RunStorageError
from smartregression.contracts.stages import InventoryPayload, RunIdentity, StageResult
from smartregression.core.execution.inventory import MAX_INVENTORY_BYTES, MAX_TESTS
from smartregression.core.git.snapshots import canonical_json


class InventoryMetadataError(ValueError):
    def __init__(self):
        super().__init__("inventory_metadata_invalid")


class UnsupportedTestId(InventoryMetadataError):
    def __init__(self):
        ValueError.__init__(self, "unsupported_test_id")


class InventoryConflict(RunStorageError):
    code = "inventory_storage_conflict"


def _identifier(value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise InventoryMetadataError()
    try:
        if "\0" in value or len(value.encode("utf-8")) > 512:
            raise InventoryMetadataError()
    except UnicodeError:
        raise InventoryMetadataError() from None


def test_id_digest(value: str) -> str:
    try:
        if type(value) is not str or not value or "\0" in value:
            raise UnsupportedTestId()
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
    except UnicodeError:
        raise UnsupportedTestId() from None


@dataclass(frozen=True)
class InventoryConfiguration:
    collector_version: str
    profile_name: str
    image_id: str | None
    worker_sha256: str
    seccomp_sha256: str
    dependencies_sha256: str
    python_version: str = "3.14.3"
    pytest_version: str = "9.1.1"
    plugins: tuple[str, ...] = ()
    timeout_seconds: int = 60
    memory_mib: int = 512
    pids: int = 64
    tmpfs_mib: int = 64
    output_bytes: int = 524288
    cpus: int = 1
    network: str = "none"

    def canonical_bytes(self) -> bytes:
        if (
            not all(
                isinstance(x, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", x)
                for x in (self.collector_version, self.profile_name)
            )
            or self.image_id is not None
            and not re.fullmatch(r"sha256:[0-9a-f]{64}", self.image_id)
            or not all(
                isinstance(x, str) and re.fullmatch(r"[0-9a-f]{64}", x)
                for x in (self.worker_sha256, self.seccomp_sha256, self.dependencies_sha256)
            )
            or self.python_version != "3.14.3"
            or self.pytest_version != "9.1.1"
            or type(self.plugins) is not tuple
            or self.plugins not in ((), ("pytest_cov.plugin",))
            or self.network != "none"
            or any(
                type(value) is not int or value != expected
                for value, expected in (
                    (self.timeout_seconds, 60),
                    (self.memory_mib, 512),
                    (self.pids, 64),
                    (self.tmpfs_mib, 64),
                    (self.output_bytes, 524288),
                    (self.cpus, 1),
                )
            )
        ):
            raise InventoryMetadataError()
        return canonical_json(asdict(self))

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


@dataclass(frozen=True)
class InventoryWrite:
    identity_json: str
    inventory_id: str
    stage_json: str
    configuration_json: str
    configuration_sha256: str
    exit_code: int | None = None
    duration_seconds: float | None = None
    diagnostic_artifact_id: str | None = None

    @property
    def identity(self) -> RunIdentity:
        return RunIdentity.model_validate_json(self.identity_json)

    @property
    def stage(self) -> StageResult[InventoryPayload]:
        return StageResult[InventoryPayload].model_validate_json(self.stage_json)

    @property
    def configuration(self) -> InventoryConfiguration:
        value = json.loads(self.configuration_json)
        value["plugins"] = tuple(value["plugins"])
        return InventoryConfiguration(**value)


def prepare_inventory(
    *,
    identity: RunIdentity,
    inventory_id: str,
    stage: StageResult[InventoryPayload],
    configuration: InventoryConfiguration,
    exit_code: int | None = None,
    duration_seconds: float | None = None,
    diagnostic_artifact_id: str | None = None,
) -> InventoryWrite:
    return validate_inventory_write(
        InventoryWrite(
            canonical_json(identity.model_dump(mode="json")).decode(),
            inventory_id,
            canonical_json(stage.model_dump(mode="json")).decode(),
            configuration.canonical_bytes().decode(),
            configuration.digest,
            exit_code,
            duration_seconds,
            diagnostic_artifact_id,
        )
    )


def validate_inventory_write(write: InventoryWrite) -> InventoryWrite:
    try:
        if not isinstance(write, InventoryWrite):
            raise InventoryMetadataError()
        identity, stage, config = write.identity, write.stage, write.configuration
        _identifier(identity.run_id)
        _identifier(write.inventory_id)
        if write.diagnostic_artifact_id is not None:
            _identifier(write.diagnostic_artifact_id)
        if (
            canonical_json(identity.model_dump(mode="json")).decode() != write.identity_json
            or canonical_json(stage.model_dump(mode="json")).decode() != write.stage_json
            or config.canonical_bytes().decode() != write.configuration_json
            or config.digest != write.configuration_sha256
            or write.exit_code is not None
            and (type(write.exit_code) is not int or write.exit_code not in range(256))
            or write.duration_seconds is not None
            and (
                type(write.duration_seconds) not in (int, float)
                or not math.isfinite(write.duration_seconds)
                or write.duration_seconds < 0
            )
        ):
            raise InventoryMetadataError()
        if stage.data is not None:
            if stage.data.snapshot != identity.target or config.image_id is None:
                raise InventoryMetadataError()
            ids = stage.data.test_ids
            # Duplicate IDs are checked by the canonical model. Reject unsupported
            # PostgreSQL text explicitly; never replace, truncate or normalize.
            for value in ids:
                test_id_digest(value)
            if (
                len(ids) > MAX_TESTS
                or sum(len(x.encode("utf-8")) for x in ids) > MAX_INVENTORY_BYTES
            ):
                raise InventoryMetadataError()
            if (stage.status == "partial") != (stage.data.completeness == "partial"):
                raise InventoryMetadataError()
        return write
    except UnsupportedTestId:
        raise
    except ValueError, TypeError, KeyError, AttributeError, ValidationError:
        raise InventoryMetadataError() from None


class InventoryStore(Protocol):
    def save(self, write: InventoryWrite) -> None: ...

    def load(
        self, identity: RunIdentity, inventory_id: str, configuration_sha256: str
    ) -> InventoryWrite | None: ...


def require_complete_inventory_ids(
    write: InventoryWrite, *, identity: RunIdentity, configuration_sha256: str
) -> tuple[str, ...]:
    """Execution/selection guard; partial IDs remain available only as partial data."""
    write = validate_inventory_write(write)
    if write.identity != identity or write.configuration_sha256 != configuration_sha256:
        raise InventoryConflict()
    if write.stage.status != "completed" or write.stage.data.completeness != "complete":
        raise InventoryMetadataError()
    return tuple(write.stage.data.test_ids)

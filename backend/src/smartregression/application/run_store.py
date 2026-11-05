"""Run/report metadata preparation and port, independent of infrastructure imports.

The caller owns repository authorization, trusted snapshot acquisition and exclusive
report publication. These values describe a write; they do not prove persistence or
artifact availability. SQL schema/constraints/adapter acceptance remain separate.
"""

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, field
from typing import Literal, Protocol

from pydantic import ValidationError

from smartregression.contracts.stages import (
    RunIdentity,
    StageAnalysisReport,
    StageResult,
    StageStatus,
)
from smartregression.core.git.snapshots import (
    SnapshotLimits,
    SnapshotManifest,
    canonical_json,
    validate_snapshot_paths,
)

_STAGES = frozenset(
    {
        "snapshots",
        "changes",
        "graph",
        "impact",
        "inventory",
        "retrieval",
        "evidence",
        "review_ordering",
    }
)
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+/-]{0,127}")


class RunStorageError(RuntimeError):
    code = "run_storage_failed"

    def __init__(self) -> None:
        super().__init__(self.code)


class RunConflict(RunStorageError):
    """Existing scoped identity/config/report differs; an identical retry is a no-op."""

    code = "run_storage_conflict"


class RunMetadataError(ValueError):
    """Unsupported/inconsistent persistence input, not an analysis failure."""

    code = "run_metadata_invalid"

    def __init__(self) -> None:
        super().__init__(self.code)


def _metadata_id(value: str) -> None:
    try:
        valid = (
            isinstance(value, str)
            and value == value.strip()
            and bool(value)
            and ("\0" not in value and len(value.encode("utf-8")) <= 512)
        )
    except UnicodeError:
        valid = False
    if not valid:
        raise RunMetadataError()


def _version(value: str | None) -> None:
    if value is not None and (not isinstance(value, str) or not _VERSION.fullmatch(value)):
        raise RunMetadataError()


@dataclass(frozen=True, repr=False)
class RunConfiguration:
    """Allowlisted actual execution settings, supplied by the trusted caller.

    Unknown versions stay None. No arbitrary options/DSN/source/outcome dictionaries.
    The analysis workflow captures these from its execution; independently supplied
    settings still cannot prove that a producer used them.
    """

    application_version: str | None
    snapshot_limits: SnapshotLimits
    python_source_limit_bytes: int
    producer_versions: tuple[tuple[str, str | None], ...] = ()
    graph_policy: Literal["target_imports"] = "target_imports"
    comparison_mode: Literal["direct_two_tree"] = "direct_two_tree"
    inventory_configuration_digest: str | None = None

    def canonical_bytes(self) -> bytes:
        _version(self.application_version)
        if self.inventory_configuration_digest is not None and (
            not isinstance(self.inventory_configuration_digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", self.inventory_configuration_digest)
        ):
            raise RunMetadataError()
        if (
            not isinstance(self.snapshot_limits, SnapshotLimits)
            or type(self.python_source_limit_bytes) is not int
            or not 1 <= self.python_source_limit_bytes <= 1_000_000
            or self.graph_policy != "target_imports"
            or self.comparison_mode != "direct_two_tree"
            or type(self.producer_versions) is not tuple
        ):
            raise RunMetadataError()
        versions = {}
        for item in self.producer_versions:
            if type(item) is not tuple or len(item) != 2:
                raise RunMetadataError()
            name, version = item
            if not isinstance(name, str) or name not in _STAGES or name in versions:
                raise RunMetadataError()
            _version(version)
            versions[name] = version
        content = canonical_json(
            {
                "application_version": self.application_version,
                "comparison_mode": self.comparison_mode,
                "snapshot_limits": asdict(self.snapshot_limits),
                "python_source_limit_bytes": self.python_source_limit_bytes,
                "graph_policy": self.graph_policy,
                "producer_versions": versions,
                **(
                    {"inventory_configuration_digest": self.inventory_configuration_digest}
                    if self.inventory_configuration_digest is not None
                    else {}
                ),
            }
        )
        if len(content) > 65536:
            raise RunMetadataError()
        return content


@dataclass(frozen=True)
class ReportArtifact:
    """Reference to already published bytes; does not read/authorize a filesystem path.

    Kind=report_json, schema=2.0.0, media_type=application/json, access=repository.
    The write's identity supplies repository/run scope; no independent foreign scope.
    Trusted publisher/reader must resolve under a controlled artifact root and reject
    links/junctions, missing/corrupt files. This descriptor is not proof of publication.
    """

    artifact_id: str
    storage_key: str = field(repr=False)
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        _metadata_id(self.artifact_id)
        if not isinstance(self.storage_key, str):
            raise RunMetadataError()
        try:
            validate_snapshot_paths([self.storage_key])
        except ValueError, TypeError:
            raise RunMetadataError() from None
        if (
            not isinstance(self.sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", self.sha256)
            or type(self.size_bytes) is not int
            or not 0 <= self.size_bytes <= 2**63 - 1
        ):
            raise RunMetadataError()


@dataclass(frozen=True)
class SnapshotMetadata:
    repository_id: str
    commit_sha: str
    snapshot_id: str
    manifest_version: str
    materializer_version: str


@dataclass(frozen=True)
class RunReportWrite:
    """Prepared immutable values for the SQL adapter, not a public report DTO.

    JSON bytes are canonical metadata only; no report body/source is stored here.
    An adapter must accept values prepared/revalidated at the application boundary,
    enforce scoped immutable rows and compare retries in one bounded transaction.
    Unknown metrics remain None. No method here claims successful persistence.
    """

    identity: RunIdentity
    report_id: str
    data_kind: Literal["demo", "real"]
    configuration_json: bytes = field(repr=False)
    stage_summary_json: bytes = field(repr=False)
    snapshots: tuple[SnapshotMetadata, ...]
    artifact: ReportArtifact
    analysis_status: StageStatus
    analysis_duration_seconds: float | None
    llm_cost_usd: float | None

    @property
    def configuration_sha256(self) -> str:
        return hashlib.sha256(self.configuration_json).hexdigest()


class RunReportStore(Protocol):
    """Save prerequisites/catalog/summary atomically for an authorized existing repo.

    Key=(repository_id, run_id, report_id); run identity/config and artifact identities
    are immutable. Exact retry is a no-op, any disagreement raises RunConflict.
    Unavailable/corrupt storage raises RunStorageError, never returns success. SQL
    implementations must handle concurrency/commit ambiguity; this port does not.
    It never loads a report or infers completion from metadata. Full report reading
    and optional EvidenceBundle persistence are separate capabilities.
    """

    def save(self, write: RunReportWrite) -> None: ...


def prepare_run_report(
    *,
    report: StageAnalysisReport,
    configuration: RunConfiguration,
    snapshot_manifests: tuple[SnapshotManifest, ...],
    artifact: ReportArtifact,
    published_report_bytes: bytes,
) -> RunReportWrite:
    """Revalidate nested report data and its exact published-byte digest before SQL.

    Manifests must come from validated acquisition, not offline report guesses.
    Snapshot file/hash verification and repository authorization remain caller-owned.
    Reading/comparing supplied bytes does not verify the file actually exists.
    """
    if (
        not isinstance(report, StageAnalysisReport)
        or not isinstance(configuration, RunConfiguration)
        or not isinstance(artifact, ReportArtifact)
        or not isinstance(published_report_bytes, bytes)
        or type(snapshot_manifests) is not tuple
        or any(not isinstance(m, SnapshotManifest) for m in snapshot_manifests)
    ):
        raise RunMetadataError()
    try:
        checked = StageAnalysisReport.model_validate_json(report.model_dump_json())
        stored = StageAnalysisReport.model_validate_json(published_report_bytes)
        if checked != stored or (
            hashlib.sha256(published_report_bytes).hexdigest() != artifact.sha256
            or len(published_report_bytes) != artifact.size_bytes
        ):
            raise RunMetadataError()
        _metadata_id(checked.identity.run_id)
        _metadata_id(checked.report_id)
        # Revalidate even descriptors forged with dataclass replacement/object mutation.
        ReportArtifact(
            artifact.artifact_id, artifact.storage_key, artifact.sha256, artifact.size_bytes
        )
        config_json = configuration.canonical_bytes()
        if configuration.comparison_mode != checked.identity.comparison_mode:
            raise RunMetadataError()
        snapshots = _snapshot_metadata(checked.identity, snapshot_manifests)
        summary = canonical_json(
            {
                name: result.model_dump(mode="json", exclude={"data"})
                for name, result in checked.stages
            }
        )
        if len(summary) > 262144:
            raise RunMetadataError()
    except ValidationError, ValueError, TypeError, UnicodeError, RecursionError:
        raise RunMetadataError() from None
    return RunReportWrite(
        checked.identity,
        checked.report_id,
        checked.data_kind,
        config_json,
        summary,
        snapshots,
        artifact,
        checked.analysis_status,
        checked.analysis_duration_seconds,
        checked.llm_cost_usd,
    )


def _snapshot_metadata(
    identity: RunIdentity,
    manifests: tuple[SnapshotManifest, ...],
) -> tuple[SnapshotMetadata, ...]:
    required = {
        (s.repository_id, s.commit, s.snapshot_id)
        for s in (identity.base, identity.target)
        if s.snapshot_id is not None
    }
    found = {}
    for manifest in manifests:
        key = (manifest.repository_id, manifest.commit, manifest.snapshot_id)
        _version(manifest.schema_version)
        _version(manifest.materializer_version)
        if key not in required or not manifest.schema_version or not manifest.materializer_version:
            raise RunMetadataError()
        metadata = SnapshotMetadata(*key, manifest.schema_version, manifest.materializer_version)
        if key in found and found[key] != metadata:
            raise RunMetadataError()
        found[key] = metadata
    if set(found) != required:
        raise RunMetadataError()
    return tuple(found[key] for key in sorted(found))


def validate_run_report_write(write: RunReportWrite) -> RunReportWrite:
    """Revalidate prepared metadata at the SQL boundary; no source/file verification.

    Direct dataclass construction/replacement must not bypass preparation. This
    detaches mutable Pydantic identity values and requires canonical bounded bytes.
    """
    try:
        if not isinstance(write, RunReportWrite):
            raise RunMetadataError()
        identity = RunIdentity.model_validate_json(write.identity.model_dump_json())
        if identity != write.identity:
            raise RunMetadataError()
        _metadata_id(identity.run_id)
        _metadata_id(write.report_id)
        if write.data_kind not in {"demo", "real"}:
            raise RunMetadataError()
        artifact = ReportArtifact(
            write.artifact.artifact_id,
            write.artifact.storage_key,
            write.artifact.sha256,
            write.artifact.size_bytes,
        )
        if len(artifact.storage_key.encode()) > 2048:
            raise RunMetadataError()
        if type(write.configuration_json) is not bytes or len(write.configuration_json) > 65536:
            raise RunMetadataError()
        config = json.loads(write.configuration_json)
        required = {
            "application_version",
            "comparison_mode",
            "snapshot_limits",
            "python_source_limit_bytes",
            "graph_policy",
            "producer_versions",
        }
        if set(config) not in (required, required | {"inventory_configuration_digest"}):
            raise RunMetadataError()
        rebuilt = RunConfiguration(
            config["application_version"],
            SnapshotLimits(**config["snapshot_limits"]),
            config["python_source_limit_bytes"],
            tuple(config["producer_versions"].items()),
            config["graph_policy"],
            config["comparison_mode"],
            config.get("inventory_configuration_digest"),
        )
        if (
            rebuilt.canonical_bytes() != write.configuration_json
            or rebuilt.comparison_mode != identity.comparison_mode
        ):
            raise RunMetadataError()
        if type(write.stage_summary_json) is not bytes or len(write.stage_summary_json) > 262144:
            raise RunMetadataError()
        summary = json.loads(write.stage_summary_json)
        if set(summary) != _STAGES or canonical_json(summary) != write.stage_summary_json:
            raise RunMetadataError()
        statuses = set()
        for value in summary.values():
            if set(value) != {"status", "reason", "error_code", "limitations"}:
                raise RunMetadataError()
            result = StageResult(
                **value, data={} if value["status"] in {"completed", "partial"} else None
            )
            if result.model_dump(mode="json", exclude={"data"}) != value:
                raise RunMetadataError()
            statuses.add(result.status)
        aggregate = (
            "completed"
            if statuses == {"completed"}
            else "partial"
            if statuses & {"completed", "partial"}
            else "failed"
            if "failed" in statuses
            else "not_run"
            if "not_run" in statuses
            else "not_implemented"
        )
        if aggregate != write.analysis_status:
            raise RunMetadataError()
        for measurement in (write.analysis_duration_seconds, write.llm_cost_usd):
            if measurement is not None and (
                type(measurement) not in {int, float}
                or not math.isfinite(measurement)
                or measurement < 0
            ):
                raise RunMetadataError()
        if type(write.snapshots) is not tuple or any(
            not isinstance(s, SnapshotMetadata) for s in write.snapshots
        ):
            raise RunMetadataError()
        manifests = tuple(
            SnapshotManifest(
                s.repository_id,
                s.commit_sha,
                (),
                s.snapshot_id,
                s.manifest_version,
                s.materializer_version,
            )
            for s in write.snapshots
        )
        snapshots = _snapshot_metadata(identity, manifests)
        if snapshots != write.snapshots:
            raise RunMetadataError()
    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        UnicodeError,
        RecursionError,
        OverflowError,
    ):
        raise RunMetadataError() from None
    return RunReportWrite(
        identity,
        write.report_id,
        write.data_kind,
        write.configuration_json,
        write.stage_summary_json,
        snapshots,
        artifact,
        write.analysis_status,
        write.analysis_duration_seconds,
        write.llm_cost_usd,
    )

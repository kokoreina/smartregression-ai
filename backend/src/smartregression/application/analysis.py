"""Incremental read-only analysis. Missing producers remain explicit in v2 reports."""

import ast
import re
from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from smartregression.application.changed_components import identify_changes
from smartregression.application.evidence import EVIDENCE_VERSION, explain_impact
from smartregression.application.frozen_reader import DiffSource, FrozenReader
from smartregression.application.inventory import InventoryCollector, collect_inventory
from smartregression.application.run_store import RunConfiguration
from smartregression.application.snapshots import (
    RepositoryAuthorization,
    SnapshotSource,
    prepare_snapshots,
)
from smartregression.application.stage_conversion import (
    changes_result,
    graph_result,
    identity_from_snapshots,
    review_result,
    snapshots_result,
)
from smartregression.contracts.models import Commit
from smartregression.contracts.stages import (
    AnalysisStages,
    ChangePayload,
    GraphPayload,
    RepositoryId,
    StageAnalysisReport,
    StageIssue,
    StageResult,
    StageStatus,
)
from smartregression.core.git.snapshots import SnapshotLimits, SnapshotManifest, SnapshotPair
from smartregression.core.impact.dependency_graph import build_dependency_graph
from smartregression.core.impact.potential_impact import build_potential_impact
from smartregression.core.impact.python_snapshot import MAX_PYTHON_SOURCE_BYTES
from smartregression.core.impact.review_ordering import RULE_VERSION, order_from_impact_payload

_SAFE_ERRORS = frozenset(
    {
        "unauthorized_repository",
        "invalid_commit",
        "invalid_repository_root",
        "unsupported_snapshot_entry",
        "unsafe_snapshot_path",
        "snapshot_path_collision",
        "snapshot_limit",
        "snapshot_objects_missing",
        "snapshot_mismatch",
        "git_unavailable_or_timeout",
        "output_limit",
        "unsupported_file_mode",
        "unsupported_change",
        "unsupported_path",
        "snapshot_diff_mismatch",
        "change_identity_or_version_mismatch",
        "graph_snapshot_mismatch",
        "python_parse_failed",
        "python_path_required",
        "ambiguous_module",
        "source_limit",
        "binary_source",
    }
)


class AnalysisError(ValueError):
    """Safe acquisition/request failure; there is no canonical report yet."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class AnalysisSource(SnapshotSource, DiffSource, Protocol):
    pass


@dataclass(frozen=True)
class AnalysisExecution:
    """Trusted acquisition metadata from one execution, never a public report format."""

    report: StageAnalysisReport
    configuration: RunConfiguration
    snapshot_manifests: tuple[SnapshotManifest, ...]


def _error_code(exc: ValueError, fallback: str) -> str:
    return str(exc) if str(exc) in _SAFE_ERRORS else fallback


class _GraphSourceError(ValueError):
    """A safe reason and frozen target path, without raw source/exception text."""

    def __init__(self, code: str, path: str) -> None:
        super().__init__(code)
        self.issue = StageIssue(code=code, path=path)


def _graph_sources(pair: SnapshotPair) -> tuple[dict[str, str], list[StageIssue]]:
    sources = {}
    limitations = []
    for entry, content in zip(pair.target.manifest.files, pair.target.contents, strict=True):
        if not entry.path.endswith(".py"):
            continue
        if len(content) > MAX_PYTHON_SOURCE_BYTES:
            raise _GraphSourceError("source_limit", entry.path)
        if b"\0" in content:
            raise _GraphSourceError("binary_source", entry.path)
        try:
            source = content.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise _GraphSourceError("python_source_not_utf8", entry.path) from exc
        sources[entry.path] = source
        # The baseline producer drops aliases after the first in this syntax.
        # Preserve observations, disclose the omission; do not fix H2's algorithm here.
        try:
            tree = ast.parse(source)
        except (SyntaxError, RecursionError, ValueError) as exc:
            raise _GraphSourceError("python_parse_failed", entry.path) from exc
        if any(
            isinstance(n, ast.ImportFrom) and n.level and n.module is None and len(n.names) > 1
            for n in ast.walk(tree)
        ):
            limitations.append(StageIssue(code="graph_relative_alias_omission", path=entry.path))
    return sources, limitations


def _impact_inputs(
    changes: ChangePayload, graph: GraphPayload
) -> tuple[ChangePayload, list[StageIssue]]:
    """Project target-observable origins; preserve the full diff in the original report."""
    components, omitted = [], set()
    for component in changes.components:
        if not component.path.endswith(".py"):
            omitted.add(("impact_non_python_change", component.path))
        elif component.change == "deleted":
            omitted.add(("impact_deleted_origin_target_graph", component.path))
        elif component.path not in graph.nodes:
            omitted.add(("impact_origin_not_in_graph", component.path))
        else:
            components.append(component)
    paths = {component.path for component in components}
    return ChangePayload(
        components=components, files=[f for f in changes.files if f.path in paths]
    ), [StageIssue(code=code, path=path) for code, path in sorted(omitted)]


def analyze(
    source: AnalysisSource,
    *,
    authorization: RepositoryAuthorization,
    repository_id: str,
    base: str,
    target: str,
    data_kind: Literal["demo", "real"] = "real",
    limits: SnapshotLimits | None = None,
    inventory_collector: InventoryCollector | None = None,
) -> StageAnalysisReport:
    """Compatibility boundary for callers that only need the canonical report."""
    return analyze_execution(
        source,
        authorization=authorization,
        repository_id=repository_id,
        base=base,
        target=target,
        data_kind=data_kind,
        limits=limits,
        inventory_collector=inventory_collector,
    ).report


def analyze_execution(
    source: AnalysisSource,
    *,
    authorization: RepositoryAuthorization,
    repository_id: str,
    base: str,
    target: str,
    data_kind: Literal["demo", "real"] = "real",
    limits: SnapshotLimits | None = None,
    inventory_collector: InventoryCollector | None = None,
) -> AnalysisExecution:
    """Authorize and freeze once, then call existing producers on that exact pair.

    Local CLI authorization is the operator's explicit ID/path binding, not a
    multi-user access-control service. Discovery is opt-in through an explicitly
    injected isolated collector; the default read-only flow executes no input code.
    """
    try:
        TypeAdapter(RepositoryId).validate_python(repository_id)
        TypeAdapter(Commit).validate_python(base)
        TypeAdapter(Commit).validate_python(target)
        TypeAdapter(Literal["demo", "real"]).validate_python(data_kind)
    except ValidationError as exc:
        raise AnalysisError("invalid_analysis_request") from exc
    limits = limits or SnapshotLimits()
    try:
        pair = prepare_snapshots(
            source,
            authorization=authorization,
            repository_id=repository_id,
            base=base,
            target=target,
            limits=limits,
        )
        if (
            pair.base.manifest.repository_id != repository_id
            or pair.target.manifest.repository_id != repository_id
            or pair.base.manifest.commit != base
            or pair.target.manifest.commit != target
            or pair.source_repository != str(source.repository.resolve(strict=True))
        ):
            raise ValueError("snapshot_mismatch")
        identity = identity_from_snapshots(pair, run_id=str(uuid4()))
        snapshots = snapshots_result(pair)
    except (OSError, UnicodeError) as exc:
        raise AnalysisError("snapshot_io_error") from exc
    except ValueError as exc:
        raise AnalysisError(_error_code(exc, "snapshot_acquisition_failed")) from exc

    change_version = None
    try:
        observations = identify_changes(
            FrozenReader(pair, source), repository=repository_id, base=base, target=target
        )
        changes = changes_result(observations, identity)
        change_version = observations.schema_version
    except OSError, UnicodeError:
        changes = StageResult(status="failed", error_code="change_analysis_io_error")
    except ValueError as exc:
        changes = StageResult(
            status="failed", error_code=_error_code(exc, "change_analysis_failed")
        )

    # Graph depends on snapshots, not successful diff parsing. Independent useful
    # observations survive a failed change stage; review must not use that failure.
    try:
        sources, limitations = _graph_sources(pair)
        graph = graph_result(
            build_dependency_graph(repository=repository_id, revision=target, sources=sources),
            identity.target,
        )
        if limitations:
            graph = StageResult(
                status="partial", data=graph.data, limitations=[*graph.limitations, *limitations]
            )
    except _GraphSourceError as exc:
        # Do not publish a graph from the validated prefix of a failed snapshot.
        # The issue identifies the first rejected target file, including unchanged files.
        graph = StageResult(status="failed", error_code=str(exc), limitations=[exc.issue])
    except UnicodeError:
        graph = StageResult(status="failed", error_code="python_source_not_utf8")
    except ValueError as exc:
        graph = StageResult(status="failed", error_code=_error_code(exc, "graph_analysis_failed"))

    def absent() -> StageResult:
        return StageResult(status="not_implemented", reason="producer_unavailable")

    impact = StageResult(status="not_run", reason="dependency_failed")
    evidence = StageResult(status="not_run", reason="dependency_failed")
    review = StageResult(status="not_run", reason="dependency_failed")
    if changes.data is not None and graph.data is not None:
        projected, scope_issues = _impact_inputs(changes.data, graph.data)
        inherited = [*changes.limitations, *graph.limitations, *scope_issues]
        try:
            impact = StageResult(
                status="partial" if inherited else "completed",
                data=build_potential_impact(identity, projected, graph.data),
                limitations=inherited,
            )
        except ValueError, RecursionError:
            impact = StageResult(status="failed", error_code="impact_analysis_failed")
        if impact.data is not None:
            try:
                explained, evidence = explain_impact(
                    identity, changes.data, graph.data, impact.data, pair
                )
                impact = impact.model_copy(update={"data": explained})
                if inherited:
                    evidence = StageResult(
                        status="partial",
                        data=evidence.data,
                        limitations=[*evidence.limitations, *inherited],
                    )
            except ValueError, UnicodeError, RecursionError:
                evidence = StageResult(status="failed", error_code="evidence_verification_failed")
            try:
                review = review_result(
                    order_from_impact_payload(
                        impact.data,
                        graph=graph.data,
                        limitations=[issue.code for issue in inherited],
                    ),
                    graph.data.snapshot,
                )
            except ValueError, RecursionError:
                review = StageResult(status="failed", error_code="review_ordering_failed")

    inventory_digest = None
    inventory = StageResult(status="not_run", reason="inventory_collector_not_configured")
    if inventory_collector is not None:
        try:
            before_digest = inventory_collector.configuration_digest
            inventory = collect_inventory(pair.target, identity, inventory_collector)
            after_digest = inventory_collector.configuration_digest
            if before_digest != after_digest:
                inventory = StageResult(
                    status="failed", error_code="collector_configuration_changed"
                )
            elif isinstance(before_digest, str) and re.fullmatch(r"[0-9a-f]{64}", before_digest):
                inventory_digest = before_digest
            else:
                inventory = StageResult(
                    status="failed", error_code="inventory_configuration_invalid"
                )
        except ValueError, OSError:
            inventory = StageResult(status="failed", error_code="inventory_configuration_invalid")

    stages = AnalysisStages(
        snapshots=snapshots,
        changes=changes,
        graph=graph,
        impact=impact,
        inventory=inventory,
        retrieval=absent(),
        evidence=evidence,
        review_ordering=review,
    )
    # Aggregate completeness exactly as v2 defines it; the CLI separately signals
    # stage failures that can exist inside a partial report.
    report = StageAnalysisReport(
        schema_version="2.0.0",
        report_id=str(uuid4()),
        data_kind=data_kind,
        identity=identity,
        analysis_status=aggregate_status(stages),
        stages=stages,
    )
    return AnalysisExecution(
        report=StageAnalysisReport.model_validate_json(report.model_dump_json()),
        configuration=RunConfiguration(
            application_version=None,
            snapshot_limits=limits,
            python_source_limit_bytes=MAX_PYTHON_SOURCE_BYTES,
            producer_versions=(
                ("snapshots", pair.target.manifest.schema_version),
                ("changes", change_version),
                ("graph", None),
                ("impact", None),
                ("evidence", EVIDENCE_VERSION),
                ("review_ordering", RULE_VERSION),
            ),
            inventory_configuration_digest=inventory_digest,
        ),
        snapshot_manifests=(pair.base.manifest, pair.target.manifest),
    )


def aggregate_status(stages: AnalysisStages) -> StageStatus:
    """Report completeness, never test outcomes or a repository safety verdict."""
    statuses = {getattr(stages, name).status for name in type(stages).model_fields}
    if statuses == {"completed"}:
        return "completed"
    if statuses & {"completed", "partial"}:
        return "partial"
    if "failed" in statuses:
        return "failed"
    if "not_run" in statuses:
        return "not_run"
    return "not_implemented"


def analysis_exit_code(report: StageAnalysisReport) -> int:
    """0 complete; 1 incomplete without stage failure; 2 failure, even in partial."""
    if any(
        getattr(report.stages, name).status == "failed" for name in type(report.stages).model_fields
    ):
        return 2
    return 0 if report.analysis_status == "completed" else 1

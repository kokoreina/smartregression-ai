"""Incremental read-only analysis. Missing producers remain explicit in v2 reports."""

import ast
from typing import Literal, Protocol
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from smartregression.application.changed_components import identify_changes
from smartregression.application.frozen_reader import DiffSource, FrozenReader
from smartregression.application.inventory import InventoryCollector, collect_inventory
from smartregression.application.snapshots import (
    RepositoryAuthorization,
    SnapshotSource,
    prepare_snapshots,
)
from smartregression.application.stage_conversion import (
    changes_result,
    graph_result,
    identity_from_snapshots,
    snapshots_result,
)
from smartregression.contracts.models import Commit
from smartregression.contracts.stages import (
    AnalysisStages,
    RepositoryId,
    StageAnalysisReport,
    StageIssue,
    StageResult,
    StageStatus,
)
from smartregression.core.git.snapshots import SnapshotLimits, SnapshotPair
from smartregression.core.impact.dependency_graph import build_dependency_graph

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


def _error_code(exc: ValueError, fallback: str) -> str:
    return str(exc) if str(exc) in _SAFE_ERRORS else fallback


def _graph_sources(pair: SnapshotPair) -> tuple[dict[str, str], list[StageIssue]]:
    sources = {}
    limitations = []
    for entry, content in zip(pair.target.manifest.files, pair.target.contents, strict=True):
        if not entry.path.endswith(".py"):
            continue
        if len(content) > 256_000:
            raise ValueError("source_limit")
        if b"\0" in content:
            raise ValueError("binary_source")
        source = content.decode("utf-8", errors="strict")
        sources[entry.path] = source
        # The baseline producer drops aliases after the first in this syntax.
        # Preserve observations, disclose the omission; do not fix H2's algorithm here.
        try:
            tree = ast.parse(source)
        except (SyntaxError, RecursionError, ValueError) as exc:
            raise ValueError("python_parse_failed") from exc
        if any(
            isinstance(n, ast.ImportFrom) and n.level and n.module is None and len(n.names) > 1
            for n in ast.walk(tree)
        ):
            limitations.append(StageIssue(code="graph_relative_alias_omission", path=entry.path))
    return sources, limitations


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

    try:
        changes = changes_result(
            identify_changes(
                FrozenReader(pair, source), repository=repository_id, base=base, target=target
            ),
            identity,
        )
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
    except UnicodeError:
        graph = StageResult(status="failed", error_code="python_source_not_utf8")
    except ValueError as exc:
        graph = StageResult(status="failed", error_code=_error_code(exc, "graph_analysis_failed"))

    def absent() -> StageResult:
        return StageResult(status="not_implemented", reason="producer_unavailable")

    stages = AnalysisStages(
        snapshots=snapshots,
        changes=changes,
        graph=graph,
        impact=absent(),
        inventory=(
            collect_inventory(pair.target, identity, inventory_collector)
            if inventory_collector is not None
            else absent()
        ),
        retrieval=absent(),
        evidence=absent(),
        review_ordering=StageResult(
            status="not_run",
            reason=(
                "dependency_failed"
                if "failed" in {changes.status, graph.status}
                else "producer_review_pending"
            ),
        ),
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
    return StageAnalysisReport.model_validate_json(report.model_dump_json())


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

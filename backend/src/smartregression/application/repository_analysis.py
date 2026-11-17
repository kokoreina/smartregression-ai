"""Shared repository use case. No provider SDK, HTTP or input-code execution here."""

import hashlib
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Protocol

from smartregression.application.analysis import (
    AnalysisExecution,
    AnalysisSource,
    analyze_execution,
)
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.contracts.repository import (
    NarrativeResult,
    RepositoryAnalysisRequest,
    RepositoryAnalysisResponse,
    RepositoryOverview,
    RepositoryTree,
    RepositoryTreeRequest,
)
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.retrieval.exclusions import contains_recognized_secret


class RemoteSource(AnalysisSource, Protocol):
    def inspect(self) -> RepositoryOverview: ...

    def tree(self, sha: str) -> RepositoryTree: ...


class RepositoryNarrator(Protocol):
    def explain(self, payload: dict, *, run_id: str) -> NarrativeResult: ...


def narrative_input(
    repository: RepositoryOverview | dict,
    files: list[str],
    report: StageAnalysisReport,
    question: str = "",
) -> dict:
    """Metadata only: never include source, comments, excerpts or credentials."""
    slug = (
        repository.full_name
        if isinstance(repository, RepositoryOverview)
        else repository["full_name"]
    )
    changes = report.stages.changes.data
    graph = report.stages.graph.data
    impact = report.stages.impact.data
    observations = []
    if changes:
        for index, item in enumerate(changes.components[:50]):
            observations.append(
                dict(id=f"change-{index}", path=item.path, symbol=item.symbol, change=item.change)
            )
    if graph:
        for index, item in enumerate(graph.edges[:80]):
            observations.append(dict(id=f"import-{index}", path=item.source, imports=item.target))
    if impact:
        for index, item in enumerate(impact.candidates[:50]):
            observations.append(
                dict(
                    id=f"impact-{index}",
                    path=item.path,
                    relationship=item.relationship,
                    explanation=item.explanation,
                )
            )
    return dict(
        repository=slug,
        base=report.identity.base.commit,
        target=report.identity.target.commit,
        target_snapshot=report.identity.target.snapshot_id,
        question=question,
        files=files[:100],
        observations=observations,
        limitations=[
            "Python static imports only; no behavioral proof; no test execution.",
            "Metadata is bounded and may omit files and relations. No source code supplied.",
        ],
    )


class RepositoryService:
    def __init__(
        self,
        source_factory: Callable[[str], AbstractContextManager[RemoteSource]],
        narrator: RepositoryNarrator | None,
        publisher: Callable[[AnalysisExecution, object], None] | None = None,
    ) -> None:
        self.source_factory = source_factory
        self.narrator = narrator
        self.publisher = publisher

    def inspect(self, url: str) -> RepositoryOverview:
        with self.source_factory(url) as source:
            return source.inspect()

    def tree(self, request: RepositoryTreeRequest) -> RepositoryTree:
        with self.source_factory(request.repository_url) as source:
            return source.tree(request.commit)

    def analyze(self, request: RepositoryAnalysisRequest) -> RepositoryAnalysisResponse:
        if request.use_llm and contains_recognized_secret(request.question):
            raise ValueError("sensitive_question")
        with self.source_factory(request.repository_url) as source:
            repository = source.inspect()
            repository_id = (
                "github-" + hashlib.sha256(repository.full_name.lower().encode()).hexdigest()
            )
            execution = analyze_execution(
                source,
                authorization=RepositoryAuthorization(repository_id, source.repository),
                repository_id=repository_id,
                base=request.base,
                target=request.target,
            )
            report = execution.report
            if self.publisher is not None:
                self.publisher(execution, source.repository)
            files = [e.path for e in source.snapshot_entries(request.target)]
        narrative = NarrativeResult(status="not_run", reason="user_disabled_llm")
        context = narrative_input(repository, files, report, request.question)
        if request.use_llm:
            narrative = (
                self.narrator.explain(
                    context,
                    run_id=report.identity.run_id,
                )
                if self.narrator
                else NarrativeResult(status="failed", error_code="provider_configuration")
            )
        return RepositoryAnalysisResponse(
            repository=repository,
            files=files,
            report=report,
            narrative=narrative,
            narrative_evidence=context["observations"],
            limitations=[
                "Phân tích tĩnh Python; import là ảnh hưởng tiềm năng, chưa chứng minh hành vi.",
                "Chưa thu thập/chọn/chạy test cho repository này.",
                "Git rename được biểu diễn là xóa + thêm; submodule và symlink chưa hỗ trợ.",
                "Gemini chỉ nhận metadata có giới hạn; không gửi source code hoặc excerpt.",
                *(
                    []
                    if self.publisher
                    else ["Kết quả của luồng web này chưa được lưu vào PostgreSQL."]
                ),
            ],
        )

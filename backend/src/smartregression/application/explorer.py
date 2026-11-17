"""Acquire public snapshots explicitly, parse statically, then serve bounded owner-scoped facts."""

import hashlib
from collections.abc import Callable
from threading import BoundedSemaphore
from typing import Protocol

from smartregression.application.auth import AuthFailure
from smartregression.application.repository_errors import public_repository_error
from smartregression.contracts.snapshots import ExplorerSnapshot, SourceRange
from smartregression.core.explorer.graph import (
    PARSER_CONFIG,
    build_graph,
    call_paths,
    hotspots,
    impact,
    neighborhood,
)
from smartregression.core.explorer.policy import source_allowed
from smartregression.core.git.snapshots import validate_snapshot_paths
from smartregression.core.retrieval.exclusions import contains_recognized_secret


class ExplorerStore(Protocol):
    def project(self, owner: str, project: str): ...
    def load(self, owner: str, project: str, commit: str, config: str): ...
    def save(
        self, owner: str, project: str, snapshot: ExplorerSnapshot, sources: dict[str, str]
    ) -> None: ...


class ExplorerService:
    def __init__(self, store: ExplorerStore, source_factory: Callable, parse_javascript: Callable):
        self.store, self.source_factory, self.parse_javascript = (
            store,
            source_factory,
            parse_javascript,
        )
        self.acquisition_slots = BoundedSemaphore(2)

    def materialize(self, owner: str, project: str, commit: str) -> ExplorerSnapshot:
        self.store.project(owner, project)
        slots = self.acquisition_slots
        if not slots.acquire(blocking=False):
            raise AuthFailure("analysis_busy", 409)
        try:
            return self._materialize(owner, project, commit)
        finally:
            slots.release()

    def _materialize(self, owner: str, project: str, commit: str) -> ExplorerSnapshot:
        current = self.store.project(owner, project)
        cached = self.store.load(owner, project, commit, PARSER_CONFIG)
        if cached:
            return cached[0]
        if current.archived:
            raise AuthFailure("project_archived", 409)
        try:
            with self.source_factory(current.repository_url) as source:
                entries = source.snapshot_entries(commit)
                tree = source.tree(commit)
                sources = {}
                unsupported = []
                excluded = []
                for entry in entries:
                    raw = source.read_blob(entry.blob_id, max_bytes=1_000_000)
                    if not source_allowed(entry.path, raw):
                        excluded.append(entry.path)
                        unsupported.append(entry.path)
                        continue
                    sources[entry.path] = raw.decode("utf-8")
                repository_id = (
                    "github-"
                    + hashlib.sha256(
                        current.repository_url.removeprefix("https://github.com/").lower().encode()
                    ).hexdigest()
                )
                graph = build_graph(repository_id, commit, sources, self.parse_javascript)
                graph.coverage.unsupported_files = sorted(
                    set(graph.coverage.unsupported_files) | set(unsupported)
                )
                if unsupported:
                    graph.coverage.status = "partial"
                snapshot = ExplorerSnapshot(graph=graph, tree=tree, excluded_paths=sorted(excluded))
            self.store.save(owner, project, snapshot, sources)
            return snapshot
        except AuthFailure:
            raise
        except (ValueError, KeyError, TypeError, UnicodeError) as error:
            raise AuthFailure(
                public_repository_error(error, "explorer_snapshot_failed"), 422
            ) from None

    def read(self, owner: str, project: str, commit: str):
        self.store.project(owner, project)
        value = self.store.load(owner, project, commit, PARSER_CONFIG)
        if value is None:
            raise AuthFailure("snapshot_not_ready", 409)
        return value

    def reading_guide(self, owner: str, project: str, commit: str):
        from smartregression.core.explorer.assistance import reading_guide

        snapshot, sources = self.read(owner, project, commit)
        return reading_guide(snapshot.graph, sources)

    def search(self, owner: str, project: str, commit: str, query: str, top_k: int):
        from smartregression.core.explorer.assistance import search_features

        snapshot, sources = self.read(owner, project, commit)
        try:
            return search_features(snapshot.graph, sources, query, top_k)
        except ValueError:
            raise AuthFailure("invalid_search_query", 422) from None

    def source(
        self, owner: str, project: str, commit: str, path: str, start: int, end: int
    ) -> SourceRange:
        try:
            validate_snapshot_paths([path])
        except ValueError:
            raise AuthFailure("invalid_source_path", 422) from None
        if not 1 <= start <= end or end - start >= 200:
            raise AuthFailure("source_range_limit", 422)
        snapshot, sources = self.read(owner, project, commit)
        if path not in sources:
            raise AuthFailure("source_not_available", 404)
        lines = sources[path].splitlines()
        if start > len(lines):
            raise AuthFailure("source_range_invalid", 422)
        text = "\n".join(lines[start - 1 : end])
        if len(text.encode()) > 20000 or contains_recognized_secret(text):
            raise AuthFailure("source_not_available", 403)
        return SourceRange(
            commit=commit, path=path, line_start=start, line_end=min(end, len(lines)), content=text
        )

    def graph(
        self,
        owner: str,
        project: str,
        commit: str,
        focus=None,
        limit=150,
        direction="both",
        depth=2,
    ):
        graph = self.read(owner, project, commit)[0].graph
        try:
            return neighborhood(graph, focus, limit, direction, depth)
        except ValueError:
            raise AuthFailure("invalid_graph_query", 422) from None

    def impact(self, owner: str, project: str, commit: str, paths: set[str]):
        try:
            return impact(self.read(owner, project, commit)[0].graph, paths)
        except ValueError:
            raise AuthFailure("invalid_impact_query", 422) from None

    def hotspots(self, owner: str, project: str, commit: str):
        return hotspots(self.read(owner, project, commit)[0].graph)

    def calls(self, owner: str, project: str, commit: str, start: str, depth=10, limit=20):
        try:
            return call_paths(self.read(owner, project, commit)[0].graph, start, depth, limit)
        except ValueError:
            raise AuthFailure("invalid_call_query", 422) from None

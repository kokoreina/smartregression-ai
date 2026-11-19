"""Bounded orchestration of product runs; no input-repository execution."""

import hashlib
from collections.abc import Callable
from typing import Protocol

from smartregression.application.repository_errors import public_repository_error
from smartregression.contracts.repository import (
    RepositoryAnalysisRequest,
    RepositoryAnalysisResponse,
)
from smartregression.contracts.web_runs import RunCreate, RunPage, RunStatus, SavedRunReport, WebRun

CONFIG = {"web_analysis": "1", "graph_policy": "target_imports", "languages": ["python"]}
CONFIG_DIGEST = hashlib.sha256(b"smartregression-web-static-python-v1").hexdigest()


class WebRunStore(Protocol):
    def claim(
        self, owner: str, project: str, body: RunCreate, config: str
    ) -> tuple[WebRun, bool]: ...
    def start(self, owner: str, project: str, identity: str) -> bool: ...
    def get(self, owner: str, project: str, identity: str) -> WebRun: ...
    def list(
        self,
        owner: str,
        project: str,
        cursor: str | None,
        limit: int,
        *,
        status: RunStatus | None = None,
    ) -> RunPage: ...
    def save_static(
        self, owner: str, project: str, identity: str, payload: RepositoryAnalysisResponse
    ) -> None: ...
    def finish(self, owner: str, project: str, identity: str, error: str | None) -> None: ...
    def report(self, owner: str, project: str, identity: str) -> SavedRunReport: ...
    def interrupt(self) -> None: ...


class WebRunService:
    def __init__(self, store: WebRunStore, analyze: Callable):
        self.store, self.analyze = store, analyze

    def create(self, owner: str, project: str, body: RunCreate) -> tuple[WebRun, bool]:
        return self.store.claim(owner, project, body, CONFIG_DIGEST)

    def execute(self, owner: str, project: str, identity: str) -> None:
        if not self.store.start(owner, project, identity):
            return
        run = self.store.get(owner, project, identity)
        try:
            response = self.analyze(
                RepositoryAnalysisRequest(
                    repository_url=run.repository_url,
                    base=run.base,
                    target=run.target,
                    use_llm=False,
                )
            )
            self.store.save_static(owner, project, identity, response)
        except Exception as error:
            # The job boundary must finalize safe state without leaking source/driver errors.
            self.store.finish(
                owner, project, identity, public_repository_error(error, "analysis_failed")
            )
            return
        self.store.finish(owner, project, identity, None)

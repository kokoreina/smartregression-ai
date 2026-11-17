"""Explicit metadata AI use cases; reserve before network, never automatically retry."""

import hashlib
import json
from collections.abc import Callable
from typing import Protocol

from smartregression.application.auth import AuthFailure
from smartregression.application.repository_analysis import narrative_input
from smartregression.contracts.ai_requests import AiJob, AiQuota
from smartregression.contracts.repository import NarrativeResult
from smartregression.contracts.web_runs import AiRequest, SavedRunReport
from smartregression.core.retrieval.exclusions import contains_recognized_secret


class AiStore(Protocol):
    def reserve(
        self, owner: str, project: str, run: str, body: AiRequest, digest: str
    ) -> tuple[AiJob, bool, int, str]: ...
    def get(self, owner: str, project: str, run: str, identity: str) -> AiJob: ...
    def start(self, owner: str, identity: str) -> bool: ...
    def finish(self, owner: str, identity: str, result: NarrativeResult) -> None: ...
    def quota(self, owner: str) -> AiQuota: ...


class WebAiService:
    def __init__(
        self, store: AiStore, report: Callable[[str, str, str], SavedRunReport], explain: Callable
    ):
        self.store, self.report, self.explain = store, report, explain

    def create(self, owner: str, project: str, run: str, body: AiRequest):
        if not body.allow_metadata_egress:
            raise AuthFailure("metadata_egress_consent_required", 422)
        if contains_recognized_secret(body.question):
            raise AuthFailure("sensitive_question", 422)
        self.report(owner, project, run)
        digest = hashlib.sha256(
            json.dumps(
                {"run": run, "question": body.question, "action": "commit"}, sort_keys=True
            ).encode()
        ).hexdigest()
        return self.store.reserve(owner, project, run, body, digest)

    def execute(
        self,
        owner: str,
        project: str,
        run: str,
        identity: str,
        batch: int,
        campaign: str,
        question: str,
    ) -> None:
        if not self.store.start(owner, identity):
            return
        try:
            saved = self.report(owner, project, run).payload
            context = narrative_input(saved.repository, saved.files, saved.report, question)
            result = self.explain(context, identity, batch, campaign)
        except Exception:
            result = NarrativeResult(status="failed", error_code="provider_configuration")
        self.store.finish(owner, identity, result)

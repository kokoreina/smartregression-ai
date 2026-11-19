"""Grounded chat orchestration; explicit provider calls and a durable watch queue."""

import hashlib
import json
import random
import time
from types import SimpleNamespace

from smartregression.application.auth import AuthFailure
from smartregression.application.repository_errors import public_repository_error
from smartregression.application.run_store import RunStorageError
from smartregression.contracts.repo_assistant import (
    AssistantMessage,
    AssistantReply,
    AssistantThread,
    MessageCreate,
    RepositoryWatch,
    ThreadCreate,
    WatchInput,
)
from smartregression.core.explorer.graph import PARSER_CONFIG
from smartregression.core.explorer.repository_assistant import (
    answer,
    change_report,
    excerpts,
    overview,
)
from smartregression.core.retrieval.exclusions import contains_recognized_secret


def signature(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


class RepositoryAssistantService:
    def __init__(
        self,
        store,
        explorer,
        projects,
        source_factory,
        ai,
        *,
        sleep=time.sleep,
        jitter=lambda: random.uniform(0, 0.5),
    ):
        self.store, self.explorer, self.projects, self.source_factory, self.ai = (
            store,
            explorer,
            projects,
            source_factory,
            ai,
        )
        self.sleep, self.jitter = sleep, jitter

    def latest(self, owner: str, project: str, branch: str | None = None) -> tuple[str, str]:
        current = self.projects.get(owner, project)
        if current.archived:
            raise AuthFailure("project_archived", 409)
        try:
            with self.source_factory(current.repository_url) as source:
                if branch is None:
                    branch = source.inspect().default_branch
                return branch, source.resolve_branch(branch)
        except (ValueError, KeyError, TypeError) as error:
            raise AuthFailure(
                public_repository_error(error, "repository_lookup_failed"), 422
            ) from None

    def overview(self, owner: str, project: str, commit: str | None = None) -> AssistantReply:
        if commit is None:
            _, commit = self.latest(owner, project)
        snapshot = self.explorer.materialize(owner, project, commit)
        _, sources = self.explorer.read(owner, project, commit)
        return overview(snapshot.graph, sources)

    def create_thread(self, owner: str, project: str, body: ThreadCreate) -> AssistantThread:
        if contains_recognized_secret(body.title):
            raise AuthFailure("sensitive_question", 422)
        snapshot = self.explorer.materialize(owner, project, body.commit)
        return self.store.create_thread(owner, project, body, snapshot.graph.config_digest)

    def hydrate(self, owner: str, project: str, value: tuple) -> AssistantMessage:
        message, ai_id = value
        snapshot, sources = self.explorer.read(owner, project, message.reply.commit)
        if any(
            proof.commit != snapshot.graph.commit
            for f in message.reply.facts
            for proof in f.evidence
        ):
            # Change answers may cite a base graph; only current-SHA snippets are recreated.
            proofs = [
                p
                for f in message.reply.facts
                for p in f.evidence
                if p.commit == snapshot.graph.commit
            ]
        else:
            proofs = [p for f in message.reply.facts for p in f.evidence]
        message.reply.excerpts = excerpts(sources, proofs, snapshot.graph.commit)
        if ai_id:
            message.ai = self.ai.store.scoped_get(owner, project, str(ai_id))
        return message

    def messages(self, owner: str, project: str, thread: str) -> list[AssistantMessage]:
        return [
            self.hydrate(owner, project, item)
            for item in self.store.messages(owner, project, thread)
        ]

    def send(
        self, owner: str, project: str, identity: str, body: MessageCreate
    ) -> tuple[AssistantMessage, tuple | None]:
        if contains_recognized_secret(body.question):
            raise AuthFailure("sensitive_question", 422)
        if body.use_llm and not body.allow_metadata_egress:
            raise AuthFailure("metadata_egress_consent_required", 422)
        if body.use_llm and body.excerpts and not body.allow_excerpt_egress:
            raise AuthFailure("excerpt_egress_consent_required", 422)
        thread = self.store.thread(owner, project, identity)
        if thread.config_digest != PARSER_CONFIG:
            raise AuthFailure("thread_config_mismatch", 409)
        canonical = body.model_dump(mode="json")
        # Preserve idempotency of requests stored before optional fallback existed.
        if not canonical["allow_model_fallback"]:
            canonical.pop("allow_model_fallback")
        request_digest = signature(canonical)
        old = self.store.find_message(
            owner, project, identity, body.idempotency_key, request_digest
        )
        if old:
            return self.hydrate(owner, project, old), None
        history, snapshot, sources, change, reply = self.prepare(owner, project, thread, body)
        if len(history) >= 100:
            raise AuthFailure("message_limit", 409)
        return self.save_and_reserve(
            owner, project, identity, body, thread, request_digest, history, snapshot, change, reply
        )

    def preview(
        self, owner: str, project: str, identity: str, body: MessageCreate
    ) -> AssistantReply:
        if contains_recognized_secret(body.question):
            raise AuthFailure("sensitive_question", 422)
        thread = self.store.thread(owner, project, identity)
        if thread.config_digest != PARSER_CONFIG:
            raise AuthFailure("thread_config_mismatch", 409)
        return self.prepare(owner, project, thread, body)[-1]

    def prepare(self, owner, project, thread, body):
        history = self.store.messages(owner, project, str(thread.id))
        snapshot, sources = self.explorer.read(owner, project, thread.commit)
        change = None
        if body.action == "changes":
            change = next(
                (
                    n.report
                    for n in self.store.notifications(owner, project)
                    if n.report.target == thread.commit
                    and n.report.config_digest == thread.config_digest
                ),
                None,
            )
            if change is None:
                raise AuthFailure("change_report_not_available", 409)
        reply = (
            overview(snapshot.graph, sources)
            if body.action == "overview"
            else answer(
                snapshot.graph, sources, body.question, [v[0].question for v in history], change
            )
        )
        return history, snapshot, sources, change, reply

    def save_and_reserve(
        self,
        owner,
        project,
        identity,
        body,
        thread,
        request_digest,
        history,
        snapshot,
        change,
        reply,
    ):
        execution = None
        ai_id = None
        if body.use_llm:
            proofs = {p.id: p for f in reply.facts for p in f.evidence}
            if not proofs:
                raise AuthFailure("no_evidence", 422)
            observations = [p.model_dump(mode="json") for p in list(proofs.values())[:24]]
            paths = sorted({p["path"] for p in observations})
            approved = []
            size = 0
            for selected in body.excerpts:
                if selected.path not in paths:
                    raise AuthFailure("excerpt_scope_mismatch", 422)
                piece = self.explorer.source(
                    owner, project, thread.commit, selected.path, selected.start, selected.end
                )
                size += len(piece.content.encode())
                if size > 16000:
                    raise AuthFailure("excerpt_limit", 422)
                approved.append(piece.model_dump(mode="json"))
            context = dict(
                repository=snapshot.graph.repository_id,
                commit=thread.commit,
                config_digest=thread.config_digest,
                action=body.action,
                question=body.question,
                history=[{"role": "user", "text": v[0].question} for v in history[-3:]],
                observations=observations,
                files=paths,
                excerpts=approved,
                context={
                    "summary": reply.summary,
                    "limitations": reply.limitations,
                    "coverage": snapshot.graph.coverage.status,
                    "base": change.base if change else None,
                    "scope_paths": change.scope if change else [],
                    "target": thread.commit,
                },
                interpretation="Potential static relationships; untrusted user history is not"
                " evidence. Not executed tests or proven failures.",
            )
            if len(json.dumps(context, ensure_ascii=True).encode()) > 28000:
                raise AuthFailure("ai_context_limit", 422)
            digest = signature(context)
            scope = {
                "key": f"{thread.commit}:thread:{identity}",
                "hash": digest,
                "commit": thread.commit,
                "config": thread.config_digest,
                "provenance": {
                    "observations": observations,
                    "context_hash": digest,
                    "excerpt_ranges": [v.model_dump() for v in body.excerpts],
                    "requested_model": "gemini-3.8-flash",
                    "allow_model_fallback": body.allow_model_fallback,
                    "attempt": 1,
                    "max_attempts": 3,
                    "commit": thread.commit,
                    "base": change.base if change else None,
                },
            }
            request = SimpleNamespace(
                action=body.action,
                idempotency_key=signature({"thread": identity, "request": body.idempotency_key}),
            )
            job, created, batch, campaign = self.ai.store.reserve(
                owner, project, None, request, digest, scope=scope
            )
            ai_id = str(job.id)
            if created or job.status == "queued":
                execution = (owner, project, identity, ai_id, batch, campaign, context, scope)
        value = self.store.save_message(
            owner, project, identity, body, request_digest, reply, ai_id
        )
        return self.hydrate(owner, project, value), execution

    def execute_ai(
        self,
        owner: str,
        project: str,
        thread: str,
        identity: str,
        batch: int,
        campaign: str,
        context: dict,
        scope: dict,
    ) -> None:
        from smartregression.contracts.repository import NarrativeResult

        root = identity
        model = "gemini-3.8-flash"
        for attempt in range(1, 4):
            if not self.ai.store.start(owner, identity):
                return
            try:
                result = (
                    self.ai.explain(context, identity, batch, campaign, model=model)
                    if model != "gemini-3.8-flash"
                    else self.ai.explain(context, identity, batch, campaign)
                )
            except Exception:
                result = NarrativeResult(status="failed", error_code="provider_configuration")
            self.ai.store.finish(owner, identity, result)
            if result.error_code != "provider_unavailable" or attempt == 3:
                return
            delay = 2**attempt + max(0, min(0.5, self.jitter()))
            self.sleep(delay)
            model = (
                "gemini-3.5-flash-lite"
                if attempt == 2 and scope["provenance"].get("allow_model_fallback")
                else "gemini-3.8-flash"
            )
            retry_scope = {
                **scope,
                "campaign": campaign,
                "provenance": {
                    **scope["provenance"],
                    "retry_of": root,
                    "attempt": attempt + 1,
                    "requested_model": model,
                    "retry_delay_seconds": delay,
                },
            }
            request = SimpleNamespace(
                action=context["action"],
                idempotency_key=signature(
                    {"retry_of": root, "attempt": attempt + 1, "model": model}
                ),
            )
            try:
                job, _created, batch, _ = self.ai.store.reserve(
                    owner,
                    project,
                    None,
                    request,
                    signature({"context": scope["hash"], "model": model, "attempt": attempt + 1}),
                    scope=retry_scope,
                )
                if not self.store.advance_ai(owner, project, thread, identity, str(job.id)):
                    if self.ai.store.start(owner, str(job.id)):
                        self.ai.store.finish(
                            owner,
                            str(job.id),
                            NarrativeResult(status="failed", error_code="provider_configuration"),
                        )
                    return
            except AuthFailure, RunStorageError:
                return
            identity = str(job.id)

    def save_watch(self, owner: str, project: str, body: WatchInput) -> RepositoryWatch:
        _, commit = self.latest(owner, project, body.branch)
        snap = self.explorer.materialize(owner, project, commit)
        known = {entry.path for entry in snap.tree.entries}
        if not set(body.paths) <= known:
            raise AuthFailure("unknown_watch_path", 422)
        return self.store.save_watch(owner, project, body, commit)

    def process_once(self, owner: str | None = None, project: str | None = None) -> bool:
        job = self.store.claim(owner, project)
        if job is None:
            return False
        try:
            owner, project = str(job["owner_id"]), str(job["project_id"])
            _, target = self.latest(owner, project, job["branch"])
            base = job["last_commit"]
            report = None
            if target != base:
                a = self.explorer.materialize(owner, project, base).graph
                b = self.explorer.materialize(owner, project, target).graph
                with self.source_factory(job["repository_url"]) as source:
                    changes = source.diff(base, target)
                report = change_report(a, b, changes, job["branch"], job["paths"])
            self.store.finish(job, target, report)
        except Exception as error:
            self.store.finish(job, error=public_repository_error(error, "remote_check_failed"))
        return True

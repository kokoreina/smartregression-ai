"""Real PostgreSQL conversation isolation and watch lease/publication semantics."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from backend.tests.integration.storage.test_explorer import explorer  # noqa: F401 -- shared fixture
from backend.tests.integration.storage.test_web_runs import runs  # noqa: F401 -- shared fixture
from backend.tests.unit.test_repository_web import TARGET
from sqlalchemy import text

from smartregression.adapters.storage.assistant_store import PostgresAssistantStore
from smartregression.application.auth import AuthFailure
from smartregression.contracts.repo_assistant import MessageCreate, ThreadCreate, WatchInput
from smartregression.core.explorer.repository_assistant import change_report, overview


def setup_store(request):
    service, user, stranger, project, _ = request.getfixturevalue("explorer")
    snapshot = service.materialize(user, project, TARGET)
    store = PostgresAssistantStore(service.store.engine)
    return service, store, user, stranger, project, snapshot


def test_conversation_replay_isolation_and_no_source_copy(request):
    service, store, user, stranger, project, snap = setup_store(request)
    body = ThreadCreate(commit=TARGET, idempotency_key="thread-" + uuid4().hex)
    thread = store.create_thread(user, project, body, snap.graph.config_digest)
    assert store.create_thread(user, project, body, snap.graph.config_digest) == thread
    reply = overview(snap.graph, service.read(user, project, TARGET)[1])
    question = MessageCreate(question="Explain app.py", idempotency_key="message-one")
    from smartregression.application.repo_assistant import signature

    digest = signature(question.model_dump(mode="json"))
    stored, _ = store.save_message(user, project, str(thread.id), question, digest, reply)
    assert stored.reply.excerpts == []
    assert len(store.messages(user, project, str(thread.id))) == 1
    assert (
        store.find_message(user, project, str(thread.id), question.idempotency_key, digest)[0]
        == stored
    )
    with pytest.raises(AuthFailure):
        store.messages(stranger, project, str(thread.id))
    with pytest.raises(AuthFailure, match="idempotency_conflict"):
        store.find_message(user, project, str(thread.id), question.idempotency_key, "wrong")
    store.delete_thread(user, project, str(thread.id))
    with pytest.raises(AuthFailure, match="thread_not_found"):
        store.thread(user, project, str(thread.id))


def test_manual_watch_crash_reclaim_and_atomic_notification_dedup(request):
    _, store, user, _, project, snap = setup_store(request)
    store.save_watch(user, project, WatchInput(branch="main", paths=["app.py"]), TARGET)
    store.schedule(user, project)
    job = store.claim()
    assert job and store.claim() is None
    with store.engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE smartregression.web_repo_watches SET lease_until=:past WHERE project_id=:id"
            ),
            {"past": datetime.now(UTC) - timedelta(seconds=1), "id": project},
        )
    recovered = store.claim()
    assert recovered and recovered["lease_token"] != job["lease_token"]
    report = change_report(snap.graph, snap.graph, [], "main", ["app.py"])
    assert not store.finish(job, TARGET, report)
    assert store.finish(recovered, TARGET, report)
    assert len(store.notifications(user, project)) == 1
    store.schedule(user, project)
    assert store.finish(store.claim(), TARGET, report)
    notes = store.notifications(user, project)
    assert len(notes) == 1
    store.read_notification(user, project, str(notes[0].id))
    assert store.notifications(user, project)[0].read_at


def test_watch_configuration_change_invalidates_inflight_publish(request):
    _, store, user, _, project, _ = setup_store(request)
    watch = store.save_watch(user, project, WatchInput(branch="main"), TARGET)
    store.schedule(user, project)
    old = store.claim()
    store.save_watch(user, project, WatchInput(branch="main", version=watch.version), TARGET)
    assert not store.finish(old, TARGET)
    assert store.watch(user, project).version == 2
    store.schedule(user, project)
    store.finish(store.claim(), error="github_rate_limit")
    assert store.watch(user, project).next_check_at > datetime.now(UTC) + timedelta(minutes=59)


def test_webhook_receipt_and_scheduling_commit_together(request):
    _, store, user, stranger, project, _ = setup_store(request)
    store.save_watch(user, project, WatchInput(branch="main", automatic=True), TARGET)
    identity = str(uuid4())
    assert store.delivery(identity, "a" * 64, "owner/repo", "push", "main", "owner") == (False, 1)
    assert store.watch(user, project).pending
    assert store.delivery(identity, "a" * 64, "owner/repo", "push", "main", "owner") == (True, 0)
    with pytest.raises(AuthFailure, match="webhook_delivery_conflict"):
        store.delivery(identity, "b" * 64, "owner/repo", "push", "main", "owner")
    with pytest.raises(AuthFailure):
        store.watch(stranger, project)


def test_actual_service_chat_ai_consent_and_two_sha_monitoring(request, migrated):
    from contextlib import contextmanager

    from backend.tests.unit.test_repository_web import BASE

    from smartregression.adapters.storage.project_store import PostgresProjectStore
    from smartregression.adapters.storage.web_ai_store import PostgresAiStore
    from smartregression.application.projects import ProjectService
    from smartregression.application.repo_assistant import RepositoryAssistantService
    from smartregression.application.web_ai import WebAiService
    from smartregression.contracts.ai_requests import ExcerptRange
    from smartregression.contracts.repository import NarrativeResult, RepositoryExplanation

    service, store, user, _, project, _ = setup_store(request)
    head = [BASE]

    @contextmanager
    def factory(url):
        with service.source_factory(url) as source:
            source.resolve_branch = lambda branch: head[0]
            yield source

    calls = []

    def explain(context, *args):
        calls.append(context)
        return NarrativeResult(
            status="completed",
            model="gemini-3.8-flash",
            data=RepositoryExplanation(
                summary="Supported fixture explanation", findings=[], limitations=["Not executed."]
            ),
        )

    ai = WebAiService(PostgresAiStore(store.engine), None, explain)
    assistant = RepositoryAssistantService(
        store,
        service,
        ProjectService(PostgresProjectStore(store.engine), lambda _: None),
        factory,
        ai,
    )
    initial = assistant.overview(user, project, BASE)
    assert initial.commit == BASE
    thread = assistant.create_thread(
        user, project, ThreadCreate(commit=BASE, idempotency_key="grounded-thread")
    )
    identity = str(thread.id)
    question = MessageCreate(question="math", idempotency_key="grounded-message")
    message, execution = assistant.send(user, project, identity, question)
    assert message.reply.kind == "search" and execution is None
    assert assistant.send(user, project, identity, question)[0].id == message.id
    with pytest.raises(AuthFailure, match="metadata_egress_consent_required"):
        assistant.send(
            user,
            project,
            identity,
            MessageCreate(question="math", idempotency_key="no-consent", use_llm=True),
        )
    with pytest.raises(AuthFailure, match="excerpt_egress_consent_required"):
        assistant.send(
            user,
            project,
            identity,
            MessageCreate(
                question="math",
                idempotency_key="no-source-consent",
                use_llm=True,
                allow_metadata_egress=True,
                excerpts=[ExcerptRange(path="app.py", start=1, end=2)],
            ),
        )
    campaign = "assistant-test-" + uuid4().hex
    # Product runtime cannot create its own AI budget.
    with pytest.raises(AuthFailure, match="ai_quota_exhausted"):
        assistant.send(
            user,
            project,
            identity,
            MessageCreate(
                question="math", idempotency_key=campaign, use_llm=True, allow_metadata_egress=True
            ),
        )
    assert calls == []
    with migrated[0].begin() as conn:
        conn.execute(
            text(
                "INSERT INTO smartregression.web_ai_campaigns(id,max_calls,cap_micro_usd) "
                "VALUES(:id,3,60000)"
            ),
            {"id": campaign},
        )
        conn.execute(
            text(
                "INSERT INTO smartregression.web_ai_grants"
                "(campaign_id,owner_id,max_calls,cap_micro_usd) "
                "VALUES(:id,:owner,3,60000)"
            ),
            {"id": campaign, "owner": user},
        )
    ai_question = MessageCreate(
        question="math", idempotency_key="grounded-ai", use_llm=True, allow_metadata_egress=True
    )
    ai_message, execution = assistant.send(user, project, identity, ai_question)
    assert execution is not None and ai_message.ai.status == "queued"
    assistant.execute_ai(*execution)
    assert len(calls) == 1 and calls[0]["excerpts"] == []
    assert all(p["commit"] == BASE for p in calls[0]["observations"])
    replay, _ = assistant.send(user, project, identity, ai_question)
    assert replay.ai.status == "completed" and replay.id == ai_message.id
    assistant.save_watch(user, project, WatchInput(branch="main", paths=["app.py"]))
    store.schedule(user, project)
    assert assistant.process_once() and store.notifications(user, project) == []
    head[0] = TARGET
    store.schedule(user, project)
    assert assistant.process_once()
    notes = store.notifications(user, project)
    assert len(notes) == 1 and notes[0].report.base == BASE and notes[0].report.target == TARGET
    assert store.watch(user, project).last_commit == TARGET
    store.schedule(user, project)
    assert assistant.process_once() and len(store.notifications(user, project)) == 1

    from types import SimpleNamespace

    from fastapi.testclient import TestClient

    from smartregression.api.main import create_app
    from smartregression.api.project_dependencies import product_csrf, verified_owner

    app = create_app(repo_assistant_service=assistant, mode="product")
    app.dependency_overrides[verified_owner] = lambda: SimpleNamespace(id=user)
    app.dependency_overrides[product_csrf] = lambda: None
    client = TestClient(app)
    prefix = f"/api/v1/projects/{project}/assistant"
    assert client.get(prefix + "/threads").json()[0]["commit"] == BASE
    assert client.get(prefix + "/notifications").json()[0]["report"]["target"] == TARGET
    preview_response = client.post(
        prefix + f"/threads/{identity}/preview",
        json={"question": "math", "idempotency_key": "http-preview"},
    )
    assert preview_response.status_code == 200 and preview_response.json()["kind"] == "search"
    assert len(calls) == 1  # Preview does not make another provider call.
    note_id = str(notes[0].id)
    assert client.post(prefix + f"/notifications/{note_id}/read", json={}).status_code == 204
    app.dependency_overrides[verified_owner] = lambda: SimpleNamespace(id=str(uuid4()))
    assert client.get(prefix + "/threads").status_code == 404


@pytest.mark.parametrize(
    "fallback,failures,cap,error,expected",
    [
        (False, 2, 3, "provider_unavailable", ["gemini-3.8-flash"] * 3),
        (
            True,
            2,
            3,
            "provider_unavailable",
            ["gemini-3.8-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"],
        ),
        (False, 3, 2, "provider_unavailable", ["gemini-3.8-flash"] * 2),
        (True, 3, 3, "provider_auth", ["gemini-3.8-flash"]),
    ],
)
def test_503_backoff_fallback_and_each_attempt_admitted_against_original_budget(
    request, migrated, fallback, failures, cap, error, expected
):
    from smartregression.adapters.storage.project_store import PostgresProjectStore
    from smartregression.adapters.storage.web_ai_store import PostgresAiStore
    from smartregression.application.projects import ProjectService
    from smartregression.application.repo_assistant import RepositoryAssistantService
    from smartregression.application.web_ai import WebAiService
    from smartregression.contracts.repository import NarrativeResult, RepositoryExplanation

    explorer_service, store, user, _, project, _ = setup_store(request)
    campaign = "a-g503-" + uuid4().hex
    other = "z-g503-" + uuid4().hex
    with migrated[0].begin() as conn:
        for identity, calls in [(campaign, cap), (other, 3)]:
            conn.execute(
                text(
                    "INSERT INTO smartregression.web_ai_campaigns(id,max_calls,cap_micro_usd) "
                    "VALUES(:id,:calls,:amount)"
                ),
                {"id": identity, "calls": calls, "amount": calls * 20000},
            )
            conn.execute(
                text(
                    "INSERT INTO smartregression.web_ai_grants"
                    "(campaign_id,owner_id,max_calls,cap_micro_usd) "
                    "VALUES(:id,:owner,:calls,:amount)"
                ),
                {"id": identity, "owner": user, "calls": calls, "amount": calls * 20000},
            )
    models = []
    delays = []

    def explain(context, *args, model="gemini-3.8-flash"):
        models.append(model)
        if len(models) <= failures:
            return NarrativeResult(status="failed", error_code=error)
        return NarrativeResult(
            status="completed",
            model=model,
            data=RepositoryExplanation(
                summary="Synthetic recovered answer", findings=[], limitations=["Fixture."]
            ),
        )

    ai = WebAiService(PostgresAiStore(store.engine), None, explain)
    assistant = RepositoryAssistantService(
        store,
        explorer_service,
        ProjectService(PostgresProjectStore(store.engine), lambda _: None),
        None,
        ai,
        sleep=delays.append,
        jitter=lambda: 0,
    )
    thread = assistant.create_thread(
        user, project, ThreadCreate(commit=TARGET, idempotency_key="503-thread")
    )
    body = MessageCreate(
        question="math",
        idempotency_key="503-question",
        use_llm=True,
        allow_metadata_egress=True,
        allow_model_fallback=fallback,
    )
    message, execution = assistant.send(user, project, str(thread.id), body)
    assistant.execute_ai(*execution)
    latest = assistant.messages(user, project, str(thread.id))[-1]
    assert models == expected
    assert latest.ai.provenance["requested_model"] == expected[-1]
    if error == "provider_auth":
        assert delays == []
    else:
        assert delays == [2, 4]
    with store.engine.connect() as conn:
        assert conn.scalar(
            text("SELECT count(*) FROM smartregression.web_ai_requests WHERE campaign_id=:id"),
            {"id": campaign},
        ) == len(expected)
        assert (
            conn.scalar(
                text("SELECT count(*) FROM smartregression.web_ai_requests WHERE campaign_id=:id"),
                {"id": other},
            )
            == 0
        )
    replay, repeat = assistant.send(user, project, str(thread.id), body)
    assert replay.id == message.id and replay.ai.id == latest.ai.id and repeat is None

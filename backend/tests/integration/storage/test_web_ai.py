"""Account/global reservations and replay semantics on real PostgreSQL; no paid calls."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from backend.tests.integration.storage.test_explorer import explorer  # noqa: F401
from backend.tests.integration.storage.test_web_runs import body, runs  # noqa: F401
from sqlalchemy import text

from smartregression.adapters.storage.web_ai_store import PostgresAiStore
from smartregression.application.auth import AuthFailure
from smartregression.application.web_ai import WebAiService
from smartregression.contracts.repository import NarrativeResult
from smartregression.contracts.web_runs import AiRequest


@pytest.fixture
def ai(request):
    service, user, stranger, project, _, owner = request.getfixturevalue("runs")
    run, _ = service.create(user, project, body())
    service.execute(user, project, str(run.id))
    store = PostgresAiStore(service.store.engine)
    calls = []

    def explain(*args):
        calls.append(args)
        return NarrativeResult(status="failed", error_code="provider_timeout")

    value = WebAiService(store, service.store.report, explain)
    yield value, user, stranger, project, str(run.id), owner, calls
    store.interrupt()


def grant(ai, cap=200000, calls=10):
    _, user, _, _, _, owner, _ = ai
    campaign = "test-" + uuid4().hex
    with owner.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO smartregression.web_ai_campaigns(id,max_calls,ca"
                "p_micro_usd) VALUES(:id,:calls,:cap)"
            ),
            dict(id=campaign, calls=calls, cap=cap),
        )
        conn.execute(
            text(
                "INSERT INTO smartregression.web_ai_grants(campaign_id,owner_"
                "id,max_calls,cap_micro_usd) VALUES(:id,:owner,:calls,:cap)"
            ),
            dict(id=campaign, owner=user, calls=calls, cap=cap),
        )
    return campaign


def request(key="ai-request-1"):
    return AiRequest(idempotency_key=key, allow_metadata_egress=True)


def test_scoped_assistance_shares_quota_replays_and_retains_only_metadata(ai, explorer):  # noqa: F811
    from backend.tests.unit.test_repository_web import TARGET

    from smartregression.application.assistance_ai import AssistanceAiService
    from smartregression.contracts.ai_requests import AssistanceAiRequest, ExcerptRange

    service, user, stranger, project, run, _, calls = ai
    snapshots = explorer[0]
    snapshots.materialize(user, project, TARGET)
    grant(ai, cap=20000, calls=1)
    scoped = AssistanceAiService(service.store, snapshots, None, service.explain)
    body = AssistanceAiRequest(
        commit=TARGET,
        action="file",
        path="app.py",
        idempotency_key="scoped-request-1",
        allow_metadata_egress=True,
        allow_excerpt_egress=True,
        excerpts=[ExcerptRange(path="app.py", start=1, end=2)],
    )
    job, created, batch, campaign, context = scoped.create(user, project, body)
    assert created and job.run_id is None and context["excerpts"]
    assert "content" not in str(job.provenance)
    repeated, new, *_ = scoped.create(user, project, body)
    assert not new and repeated.id == job.id
    scoped.execute(user, str(job.id), batch, campaign, context)
    assert (
        len(calls) == 1 and service.store.scoped_get(user, project, str(job.id)).status == "failed"
    )
    assert len(service.store.scoped_list(user, project, TARGET)) == 1
    with pytest.raises(AuthFailure, match="ai_quota_exhausted"):
        service.create(user, project, run, request())
    with pytest.raises(AuthFailure) as error:
        service.store.scoped_get(stranger, project, str(job.id))
    assert error.value.status == 404
    with pytest.raises(AuthFailure, match="idempotency_conflict"):
        scoped.create(user, project, body.model_copy(update={"question": "different"}))


def test_new_account_has_zero_quota_and_cross_owner_is_404(ai):
    service, user, stranger, project, run, _, calls = ai
    assert service.store.quota(user).granted_calls == 0
    with pytest.raises(AuthFailure, match="ai_quota_exhausted"):
        service.create(user, project, run, request())
    with pytest.raises(AuthFailure) as error:
        service.create(stranger, project, run, request())
    assert error.value.status == 404
    assert calls == []


def test_replay_no_provider_duplicate_and_unknown_keeps_budget(ai):
    service, user, _, project, run, _, calls = ai
    grant(ai, cap=20000, calls=1)
    job, created, batch, campaign = service.create(user, project, run, request())
    repeated, new, _, _ = service.create(user, project, run, request())
    assert created and not new and job.id == repeated.id
    service.execute(user, project, run, str(job.id), batch, campaign, request().question)
    service.execute(user, project, run, str(job.id), batch, campaign, request().question)
    assert len(calls) == 1
    assert service.store.get(user, project, run, str(job.id)).status == "failed"
    with pytest.raises(AuthFailure, match="ai_quota_exhausted"):
        service.create(user, project, run, request("ai-request-2"))
    quota = service.store.quota(user)
    assert quota.used_calls == 1 and quota.reserved_micro_usd == 20000
    assert quota.unknown_actual_count == 1 and quota.known_actual_micro_usd == 0


def test_concurrent_reservation_has_one_global_active_attempt(ai):
    service, user, _, project, run, _, _ = ai
    grant(ai)
    barrier = Barrier(4)

    def reserve(index):
        barrier.wait(timeout=10)
        try:
            service.create(user, project, run, request(f"ai-request-{index}"))
            return "created"
        except AuthFailure as error:
            return error.code

    with ThreadPoolExecutor(max_workers=4) as executor:
        outcomes = list(executor.map(reserve, range(4)))
    assert outcomes.count("created") == 1 and outcomes.count("ai_busy") == 3


def test_restart_does_not_refund_or_retry(ai):
    service, user, _, project, run, _, calls = ai
    grant(ai)
    job, *_ = service.create(user, project, run, request())
    assert service.store.start(user, str(job.id))
    service.store.interrupt()
    assert service.store.get(user, project, run, str(job.id)).status == "failed"
    assert service.store.quota(user).unknown_actual_count == 1
    assert calls == []

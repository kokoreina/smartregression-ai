"""Real scenario persistence, retry, A/B provenance and owner isolation."""

import pytest
from backend.tests.integration.storage.test_explorer import explorer  # noqa: F401
from backend.tests.integration.storage.test_web_runs import runs  # noqa: F401
from backend.tests.unit.test_repository_web import BASE, TARGET

from smartregression.adapters.storage.scenario_store import PostgresScenarioStore
from smartregression.application.auth import AuthFailure
from smartregression.application.scenarios import ScenarioService
from smartregression.contracts.scenarios import ScenarioCreate


def test_overlay_persistence_repeat_and_comparison(request):
    engine, user, stranger, project, _ = request.getfixturevalue("explorer")
    original = engine.materialize(user, project, TARGET)
    service = ScenarioService(PostgresScenarioStore(engine.store.engine), engine)
    body = ScenarioCreate(
        baseline=TARGET,
        path="src/math.py",
        title="Add refund",
        mode="code",
        input="def add(a,b):\n    return a+b\n\ndef refund(value):\n    return value\n",
        idempotency_key="scenario-001",
    )
    first = service.create(user, project, body)
    assert any(n.symbol == "refund" for n in first.delta.added_nodes)
    assert first.graph.overlay_digest == first.input_digest
    assert any(
        e.source_kind == "overlay"
        for n in first.graph.nodes
        if (e := n.evidence) and n.path == body.path
    )
    repeated = service.create(user, project, body)
    assert repeated.id == first.id
    assert engine.read(user, project, TARGET)[0] == original
    second = service.create(
        user,
        project,
        body.model_copy(update={"idempotency_key": "scenario-002", "title": "Alternative B"}),
    )
    compared = service.compare(user, project, str(first.id), str(second.id))
    assert compared.added_affected == [] and compared.removed_affected == []
    assert compared.interpretation == "no_safety_ranking"
    with pytest.raises(AuthFailure, match="idempotency_conflict"):
        service.create(user, project, body.model_copy(update={"input": "def other(): pass"}))
    with pytest.raises(AuthFailure) as error:
        service.store.get(stranger, project, str(first.id))
    assert error.value.status == 404


def test_description_has_no_static_percentage_and_wrong_baseline_rejected(request):
    engine, user, _, project, _ = request.getfixturevalue("explorer")
    engine.materialize(user, project, TARGET)
    engine.materialize(user, project, BASE)
    service = ScenarioService(PostgresScenarioStore(engine.store.engine), engine)
    body = ScenarioCreate(
        baseline=TARGET,
        path="app.py",
        title="Hypothesis",
        mode="description",
        input="Add a payment method",
        idempotency_key="hypothesis-001",
    )
    first = service.create(user, project, body)
    assert first.impact is None and first.graph is None and first.narrative.status == "not_run"
    second = service.create(
        user,
        project,
        body.model_copy(update={"baseline": BASE, "idempotency_key": "hypothesis-002"}),
    )
    with pytest.raises(AuthFailure, match="scenario_baseline_mismatch"):
        service.compare(user, project, str(first.id), str(second.id))

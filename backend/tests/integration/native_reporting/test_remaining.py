"""Existing storage/security ACs on an isolated native cluster, not the user DB."""

from backend.tests.integration.storage.test_auth import (
    accounts,  # noqa: F401
    test_http_csrf_origin_session_and_cross_account_profile,
    test_register_session_verify_profile_and_hash_only_storage,
)
from backend.tests.integration.storage.test_explorer import (
    explorer,  # noqa: F401
    test_materialize_readback_replay_and_bounded_source,
    test_other_owner_cannot_materialize_read_graph_or_source,
)
from backend.tests.integration.storage.test_notes import (
    test_notes_anchor_versions_and_cross_owner,
    test_view_state_optimistic_conflict_and_owner,
)
from backend.tests.integration.storage.test_scenarios import (
    test_description_has_no_static_percentage_and_wrong_baseline_rejected,
    test_overlay_persistence_repeat_and_comparison,
)
from backend.tests.integration.storage.test_web_runs import runs  # noqa: F401

__all__ = [
    "test_http_csrf_origin_session_and_cross_account_profile",
    "test_register_session_verify_profile_and_hash_only_storage",
    "test_materialize_readback_replay_and_bounded_source",
    "test_other_owner_cannot_materialize_read_graph_or_source",
    "test_notes_anchor_versions_and_cross_owner",
    "test_view_state_optimistic_conflict_and_owner",
    "test_description_has_no_static_percentage_and_wrong_baseline_rejected",
    "test_overlay_persistence_repeat_and_comparison",
]


def test_hypotheses_remain_unmeasured_and_scenario_comparison_is_owner_project_scoped(request):
    import pytest
    from backend.tests.unit.test_repository_web import TARGET

    from smartregression.adapters.storage.scenario_store import PostgresScenarioStore
    from smartregression.application.auth import AuthFailure
    from smartregression.application.scenarios import ScenarioService
    from smartregression.contracts.projects import ProjectCreate
    from smartregression.contracts.scenarios import ScenarioCreate

    engine, user, stranger, project, _ = request.getfixturevalue("explorer")
    engine.materialize(user, project, TARGET)
    service = ScenarioService(PostgresScenarioStore(engine.store.engine), engine)
    body = ScenarioCreate(
        baseline=TARGET,
        path="app.py",
        title="Hypothesis",
        mode="description",
        input="Explain a proposed change",
        idempotency_key="comparison-hypothesis",
    )
    a = service.create(user, project, body)
    b = service.create(
        user, project, body.model_copy(update={"idempotency_key": "comparison-other"})
    )
    equal = service.compare(user, project, str(a.id), str(b.id))
    assert equal.comparison_kind == "hypotheses" and equal.graph_delta is None
    assert equal.unresolved_left is None and equal.unresolved_right is None
    overlay = service.create(
        user,
        project,
        body.model_copy(
            update={
                "mode": "code",
                "input": "def replacement(): pass\n",
                "idempotency_key": "comparison-code",
            }
        ),
    )
    with pytest.raises(AuthFailure, match="scenario_baseline_mismatch"):
        service.compare(user, project, str(a.id), str(overlay.id))
    projects = request.getfixturevalue("runs")[4]
    other = projects.create(
        user, ProjectCreate(title="Other", repository_url="https://github.com/owner/repo")
    )
    for owner, scope in [(stranger, project), (user, str(other.id))]:
        with pytest.raises(AuthFailure) as error:
            service.compare(owner, scope, str(a.id), str(b.id))
        assert error.value.status == 404

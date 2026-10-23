from datetime import UTC, datetime, timedelta

import pytest

from smartregression.application.sprint1_prototypes import Run, check_access


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (200, "accessible"),
        (401, "unauthorized"),
        (403, "forbidden"),
        (404, "not_found_or_hidden"),
        (429, "service_error"),
        (503, "service_error"),
    ],
)
def test_access_classifies_transport_observations(status, expected):
    assert check_access("team/project", lambda identity: status) == expected


@pytest.mark.parametrize("identity", ["https://host/a/b", "../repo", "a/b/c", "a/b?token=x"])
def test_invalid_identity_never_reaches_transport(identity):
    def transport(identity):
        pytest.fail("invalid identity reached transport")

    with pytest.raises(ValueError, match="invalid_repository"):
        check_access(identity, transport)


def test_access_timeout_does_not_echo_exception():
    def transport(identity):
        raise TimeoutError("sensitive transport detail")

    assert check_access("team/project", transport) == "service_error"


def test_run_records_ordered_transitions_and_terminal_failure():
    now = datetime(2026, 10, 24, tzinfo=UTC)
    run = Run.create(now)
    running = run.transition("running", now + timedelta(seconds=1))
    failed = running.transition("failed", now + timedelta(seconds=2), "access_denied")
    assert run.state == "queued"
    assert failed.run_id == run.run_id
    assert failed.started_at == running.updated_at
    assert failed.finished_at == failed.updated_at
    assert failed.failure_reason == "access_denied"
    with pytest.raises(ValueError, match="invalid_transition"):
        failed.transition("running", now + timedelta(seconds=3))


def test_invalid_transition_time_and_reason_are_rejected():
    now = datetime(2026, 10, 24, tzinfo=UTC)
    run = Run.create(now)
    for state, at, reason in [
        ("completed", now, None),
        ("running", now - timedelta(seconds=1), None),
        ("failed", now, None),
        ("running", now, "access_denied"),
        ("failed", now, "raw secret text"),
        ("running", now.replace(tzinfo=None), None),
    ]:
        with pytest.raises(ValueError):
            run.transition(state, at, reason)


def test_success_and_duplicate_transition_policy():
    now = datetime(2026, 10, 24, tzinfo=UTC)
    first, second = Run.create(now), Run.create(now)
    assert first.run_id != second.run_id
    running = first.transition("running", now)
    with pytest.raises(ValueError, match="invalid_transition"):
        running.transition("running", now)
    done = running.transition("completed", now)
    assert done.failure_reason is None
    assert done.finished_at == now

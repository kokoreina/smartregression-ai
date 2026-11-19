"""Acceptance on real native PostgreSQL, synthetic accounts and mocked GitHub/AI."""

from backend.tests.integration.storage.test_web_ai import ai  # noqa: F401
from backend.tests.integration.storage.test_web_reporting import (
    test_csv_over_10000_rows_requires_narrower_filter,
    test_dashboard_drilldown_csv_and_owner_isolation,
    test_frozen_usage_distinguishes_null_zero_and_known_amounts,
)
from backend.tests.integration.storage.test_web_runs import runs  # noqa: F401

# Import original acceptance tests unchanged; pytest collects them in this opt-in
# native scope, using the dedicated native migrated fixture above.
__all__ = [
    "test_csv_over_10000_rows_requires_narrower_filter",
    "test_dashboard_drilldown_csv_and_owner_isolation",
    "test_frozen_usage_distinguishes_null_zero_and_known_amounts",
]


def seed_failed(owner, user, project, count, stamp):
    from uuid import uuid4

    from sqlalchemy import text

    ids = [str(uuid4()) for _ in range(count)]
    with owner.begin() as conn:
        for identity in ids:
            conn.execute(
                text("""INSERT INTO smartregression.web_runs
                (id,owner_id,project_id,repository_url,base,target,config_digest,
                 idempotency_key,request_digest,status,started_at,finished_at,error_code)
                VALUES(:id,:u,:p,'https://github.com/owner/repo',repeat('a',40),repeat('b',40),
                 repeat('c',64),:key,repeat('d',64),'failed',:t,:t,'synthetic_fixture')"""),
                {"id": identity, "key": identity, "u": user, "p": project, "t": stamp},
            )
    return ids


def test_dashboard_boundaries_frozen_rows_csv_and_owner_checks(request):
    import csv
    import io
    from datetime import UTC, datetime, timedelta

    import pytest

    from smartregression.adapters.storage.web_reporting import PostgresWebReporting
    from smartregression.application.auth import AuthFailure
    from smartregression.application.web_reporting import normalize_filter

    service, user, stranger, project, _, owner = request.getfixturevalue("runs")
    end = datetime.now(UTC) - timedelta(days=1)
    start = end - timedelta(days=1)
    ids = seed_failed(owner, user, project, 31, start)
    seed_failed(owner, user, project, 1, start - timedelta(microseconds=1))
    seed_failed(owner, user, project, 1, end)
    reports = PostgresWebReporting(service.store.engine)
    view = reports.dashboard(
        user, normalize_filter(project, start, end, "failed", "Asia/Ho_Chi_Minh")
    )
    identity = str(view.snapshot_id)
    assert view.total_runs == 31 and view.static_statuses == {"failed": 31}
    assert view.ai_statuses == {"not_run": 31}
    first = reports.page(user, identity, 0, 25)
    second = reports.page(user, identity, 25, 25)
    assert {str(r.id) for r in first.items + second.items} == set(ids)
    rows = list(csv.DictReader(io.StringIO(reports.export_csv(user, identity).lstrip("\ufeff"))))
    assert len(rows) == 31 and {r["run_id"] for r in rows} == set(ids)
    seed_failed(owner, user, project, 1, start)
    assert reports.read(user, identity)["dashboard"]["total_runs"] == 31
    assert len(reports.page(user, identity, 0, 100).items) == 31
    assert (
        reports.dashboard(user, normalize_filter(project, start, end, "failed", "UTC")).total_runs
        == 32
    )
    for action in [
        lambda: reports.read(stranger, identity),
        lambda: reports.page(stranger, identity),
        lambda: reports.export_csv(stranger, identity),
    ]:
        with pytest.raises(AuthFailure) as error:
            action()
        assert error.value.status == 404


def test_csv_preserves_frozen_filter_provenance(request):
    import csv
    import io
    from datetime import UTC, datetime, timedelta

    from smartregression.adapters.storage.web_reporting import PostgresWebReporting
    from smartregression.application.web_reporting import normalize_filter

    service, user, _, project, _, owner = request.getfixturevalue("runs")
    end = datetime.now(UTC)
    start = end - timedelta(days=1)
    seed_failed(owner, user, project, 1, start)
    reports = PostgresWebReporting(service.store.engine)
    view = reports.dashboard(user, normalize_filter(project, start, end, "failed", "UTC"))
    row = next(
        csv.DictReader(
            io.StringIO(reports.export_csv(user, str(view.snapshot_id)).lstrip("\ufeff"))
        )
    )
    assert row["view_id"] == str(view.snapshot_id)
    assert row["filter_start"] == view.filters.start.isoformat().replace("+00:00", "Z")
    assert row["filter_end"] == view.filters.end.isoformat().replace("+00:00", "Z")
    assert row["filter_status"] == "failed"


def test_history_status_filter_tie_pagination_and_owner(request):
    from datetime import UTC, datetime

    import pytest

    from smartregression.application.auth import AuthFailure

    service, user, stranger, project, _, owner = request.getfixturevalue("runs")
    ids = seed_failed(owner, user, project, 5, datetime.now(UTC))
    found = []
    cursor = None
    while True:
        page = service.store.list(user, project, cursor, 2, status="failed")
        found.extend(str(r.id) for r in page.items)
        cursor = page.next_cursor
        if not cursor:
            break
    assert len(found) == len(set(found)) == 5 and set(found) == set(ids)
    assert service.store.list(user, project, None, 2, status="completed").items == []
    with pytest.raises(AuthFailure) as error:
        service.store.list(stranger, project, None, 2, status="failed")
    assert error.value.status == 404


def test_reopen_report_is_durable_without_new_analysis(request):
    from backend.tests.integration.storage.test_web_runs import body

    from smartregression.adapters.storage.web_run_store import PostgresWebRunStore

    service, user, stranger, project, projects, _ = request.getfixturevalue("runs")
    run, _ = service.create(user, project, body())
    service.execute(user, project, str(run.id))
    first = service.store.report(user, project, str(run.id))
    second = PostgresWebRunStore(service.store.engine).report(user, project, str(run.id))
    assert first == second and first.payload.narrative.status == "not_run"
    import pytest

    from smartregression.application.auth import AuthFailure

    with pytest.raises(AuthFailure) as error:
        service.store.report(stranger, project, str(run.id))
    assert error.value.status == 404
    projects.archive(user, project, projects.get(user, project).version, True)
    assert service.store.report(user, project, str(run.id)) == first


def test_csv_contains_frozen_real_report_impact_counts_not_component_totals(request):
    import csv
    import io

    from backend.tests.integration.storage.test_web_runs import body

    from smartregression.adapters.storage.web_reporting import PostgresWebReporting
    from smartregression.application.web_reporting import normalize_filter

    service, user, _, project, _, _ = request.getfixturevalue("runs")
    run, _ = service.create(user, project, body())
    service.execute(user, project, str(run.id))
    reports = PostgresWebReporting(service.store.engine)
    view = reports.dashboard(user, normalize_filter(project, None, None, None, "UTC"))
    row = next(
        csv.DictReader(
            io.StringIO(reports.export_csv(user, str(view.snapshot_id)).lstrip("\ufeff"))
        )
    )
    # Fixture changes src/math.py; app.py imports it, src/__init__.py is unrelated.
    assert row["changed_file_count"] == "1"
    assert row["direct_file_count"] == "1"
    assert row["indirect_file_count"] == "0"
    assert row["impact_scope"] == "saved_static_report"


def test_usage_uses_request_time_static_status_and_owner_without_zeroing_unknown(request):
    from datetime import UTC, datetime, timedelta

    from backend.tests.integration.storage.test_web_ai import grant
    from backend.tests.integration.storage.test_web_ai import request as ai_request
    from sqlalchemy import text

    from smartregression.adapters.storage.web_reporting import PostgresWebReporting
    from smartregression.application.web_reporting import normalize_filter

    fixture = request.getfixturevalue("ai")
    service, user, stranger, project, run, owner, calls = fixture
    grant(fixture)
    body = ai_request("period-probe")
    job, _, batch, campaign = service.create(user, project, run, body)
    service.execute(user, project, run, str(job.id), batch, campaign, body.question)
    end = datetime.now(UTC) - timedelta(days=1)
    start = end - timedelta(days=1)
    with owner.begin() as conn:
        conn.execute(
            text("UPDATE smartregression.web_runs SET started_at=:t WHERE id=:id"),
            {"t": end + timedelta(hours=1), "id": run},
        )
        conn.execute(
            text("UPDATE smartregression.web_ai_requests SET created_at=:t WHERE id=:id"),
            {"t": start, "id": str(job.id)},
        )
    reports = PostgresWebReporting(service.store.engine)
    view = reports.dashboard(user, normalize_filter(project, start, end, None, "UTC"))
    assert view.total_runs == 0
    assert view.known_actual_micro_usd is None and view.unknown_actual_count == 1
    assert view.reservation_micro_usd == 20000
    assert len(reports.usage_page(user, str(view.snapshot_id)).items) == 1
    completed = reports.dashboard(user, normalize_filter(project, start, end, "completed", "UTC"))
    assert completed.unknown_actual_count == 1  # static completed, AI failed
    failed = reports.dashboard(user, normalize_filter(project, start, end, "failed", "UTC"))
    assert failed.unknown_actual_count == 0
    other = reports.dashboard(stranger, normalize_filter(None, start, end, None, "UTC"))
    assert other.unknown_actual_count == 0 and other.known_actual_micro_usd is None
    quota = service.store.quota(stranger)
    assert quota.granted_calls == 0 and quota.used_calls == 0
    assert len(calls) == 1  # mocked provider, no paid request

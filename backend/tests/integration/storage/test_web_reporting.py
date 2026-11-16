"""Dashboard/drilldown/exports use one owner predicate on real PostgreSQL."""

from backend.tests.integration.storage.test_web_ai import ai, grant  # noqa: F401
from backend.tests.integration.storage.test_web_ai import request as ai_request
from backend.tests.integration.storage.test_web_runs import body, runs  # noqa: F401


def test_frozen_usage_distinguishes_null_zero_and_known_amounts(request):
    from sqlalchemy import text

    from smartregression.adapters.storage.web_reporting import PostgresWebReporting
    from smartregression.application.web_reporting import normalize_filter

    fixture = request.getfixturevalue("ai")
    service, user, _, project, run, owner, _ = fixture
    grant(fixture)
    for index in range(3):
        body = ai_request(f"usage-record-{index}")
        job, _, batch, campaign = service.create(user, project, run, body)
        service.execute(user, project, run, str(job.id), batch, campaign, body.question)
        if index < 2:
            with owner.begin() as conn:
                conn.execute(
                    text(
                        "UPDATE smartregression.web_ai_requests SET actual_micro_usd=:actual "
                        "WHERE id=:id"
                    ),
                    {"actual": index * 25, "id": str(job.id)},
                )
    reporting = PostgresWebReporting(service.store.engine)
    dashboard = reporting.dashboard(user, normalize_filter(project, None, None, None, "UTC"))
    assert dashboard.known_actual_micro_usd == 25 and dashboard.unknown_actual_count == 1
    assert dashboard.reservation_micro_usd == 20000
    page = reporting.usage_page(user, str(dashboard.snapshot_id))
    assert {record.actual_micro_usd for record in page.items} == {None, 0, 25}
    # Later changes cannot rewrite the frozen summary, rows or CSV predicates.
    with owner.begin() as conn:
        conn.execute(
            text("UPDATE smartregression.web_runs SET ai_status='not_run' WHERE id=:id"),
            {"id": run},
        )
    saved = reporting.read(user, str(dashboard.snapshot_id))
    assert saved["rows"][0]["ai_status"] == "failed"


def test_csv_over_10000_rows_requires_narrower_filter(request):
    from datetime import UTC, datetime

    import pytest
    from sqlalchemy import text

    from smartregression.adapters.storage.web_reporting import PostgresWebReporting
    from smartregression.application.auth import AuthFailure
    from smartregression.application.web_reporting import normalize_filter

    service, user, _, project, _, owner = request.getfixturevalue("runs")
    with owner.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO smartregression.web_runs
                (id,owner_id,project_id,repository_url,base,target,config_digest,
                 idempotency_key,request_digest,status,started_at,finished_at,error_code)
            SELECT gen_random_uuid(),:owner,:project,'https://github.com/owner/repo',
                repeat('a',40),repeat('b',40),repeat('c',64),'bulk-'||i::text,repeat('d',64),
                'failed','2026-01-15T12:00:00Z'::timestamptz,
                '2026-01-15T12:00:01Z'::timestamptz,'synthetic_fixture'
            FROM generate_series(1,10001) i
        """),
            {"owner": user, "project": project},
        )
    reporting = PostgresWebReporting(service.store.engine)
    filters = normalize_filter(
        project, datetime(2026, 1, 14, tzinfo=UTC), datetime(2026, 1, 16, tzinfo=UTC), None, "UTC"
    )
    dashboard = reporting.dashboard(user, filters)
    assert dashboard.total_runs == 10001 and dashboard.stored_rows == 10000
    with pytest.raises(AuthFailure, match="export_row_limit"):
        reporting.export_csv(user, str(dashboard.snapshot_id))


def test_dashboard_drilldown_csv_and_owner_isolation(request):
    from smartregression.adapters.storage.web_reporting import PostgresWebReporting
    from smartregression.application.web_reporting import normalize_filter

    service, user, stranger, project, _, _ = request.getfixturevalue("runs")
    run, _ = service.create(user, project, body())
    service.execute(user, project, str(run.id))
    reporting = PostgresWebReporting(service.store.engine)
    filters = normalize_filter(project, None, None, None, "UTC", None)
    dashboard = reporting.dashboard(user, filters)
    assert dashboard.total_runs == 1 and dashboard.static_statuses == {"completed": 1}
    page = reporting.runs(user, filters, None, 25)
    assert len(page.items) == 1 and page.items[0].id == run.id
    assert reporting.csv(user, filters).count(str(run.id)) == 1
    other = reporting.dashboard(stranger, normalize_filter(None, None, None, None, "UTC", None))
    assert other.total_runs == 0 and other.known_actual_micro_usd is None

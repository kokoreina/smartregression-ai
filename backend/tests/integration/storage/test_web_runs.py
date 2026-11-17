"""Real transaction/run recovery with genuine parser/report publication, mocked GitHub only."""

from contextlib import contextmanager
from uuid import uuid4

import pytest
from backend.tests.unit.test_repository_web import BASE, TARGET, remote
from sqlalchemy import text

from smartregression.adapters.storage.analysis_store import PostgresAnalysisStore
from smartregression.adapters.storage.project_store import PostgresProjectStore
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.adapters.storage.web_run_store import PostgresWebRunStore
from smartregression.application.auth import AuthFailure
from smartregression.application.persistence import bundle_from_report, persist_report
from smartregression.application.projects import ProjectService
from smartregression.application.repository_analysis import RepositoryService
from smartregression.application.web_runs import WebRunService
from smartregression.contracts.projects import ProjectCreate
from smartregression.contracts.repository import RepositoryAnalysisRequest
from smartregression.contracts.web_runs import RunCreate


@pytest.fixture
def runs(migrated, tmp_path):
    owner, runtime, _ = migrated
    users = [str(uuid4()), str(uuid4())]
    with owner.begin() as conn:
        for user in users:
            conn.execute(
                text(
                    "INSERT INTO smartregression.web_users "
                    "(id,email,display_name,password_hash,verified) "
                    "VALUES(:id,:email,'Test','unused',true)"
                ),
                dict(id=user, email=user + "@example.com"),
            )
    projects = ProjectService(PostgresProjectStore(runtime), lambda url: None)
    project = projects.create(
        users[0], ProjectCreate(title="Demo", repository_url="https://github.com/owner/repo")
    )
    source = tmp_path / "source"
    source.mkdir()
    artifacts = tmp_path / "reports"
    artifacts.mkdir()

    @contextmanager
    def factory(url):
        yield remote(source)

    def publish(execution, repository):
        report = execution.report
        persist_report(
            ReportFiles(artifacts, source_repository=repository),
            PostgresAnalysisStore(runtime, report),
            report=report,
            configuration=execution.configuration,
            snapshot_manifests=execution.snapshot_manifests,
            artifact_id=report.report_id,
            storage_key=f"{report.identity.run_id}/{report.report_id}.json",
            bundle=bundle_from_report(report),
        )

    store = PostgresWebRunStore(runtime)
    service = WebRunService(store, RepositoryService(factory, None, publisher=publish).analyze)
    yield service, users[0], users[1], str(project.id), projects, owner
    store.interrupt()


def body(key="request-0001"):
    return RunCreate(base=BASE, target=TARGET, idempotency_key=key)


def test_duplicate_key_conflict_and_single_active_run(runs):
    service, user, _, project, *_ = runs
    first, created = service.create(user, project, body())
    second, repeated = service.create(user, project, body())
    assert created and not repeated and first.id == second.id
    with pytest.raises(AuthFailure, match="idempotency_conflict"):
        service.create(user, project, body().model_copy(update={"target": "c" * 40}))
    with pytest.raises(AuthFailure, match="analysis_busy"):
        service.create(user, project, body("different-key"))


def test_publication_readback_owner_and_restart(runs):
    service, user, stranger, project, _, owner = runs
    run, _ = service.create(user, project, body())
    assert service.store.start(user, project, str(run.id))
    payload = service.analyze(
        RepositoryAnalysisRequest(
            repository_url=run.repository_url,
            base=BASE,
            target=TARGET,
            use_llm=False,
        )
    )
    service.store.save_static(user, project, str(run.id), payload)
    service.store.finish(user, project, str(run.id), None)
    completed = service.store.get(user, project, str(run.id))
    assert completed.status == "completed" and completed.report_available
    report = service.store.report(user, project, str(run.id))
    assert report.payload.report.identity.base.commit == BASE
    assert report.payload.narrative.status == "not_run"
    reopened = PostgresWebRunStore(service.store.engine).report(user, project, str(run.id))
    assert reopened.payload == report.payload
    with pytest.raises(AuthFailure) as error:
        service.store.report(stranger, project, str(run.id))
    assert error.value.status == 404
    with owner.connect() as conn:
        assert (
            conn.scalar(
                text("SELECT count(*) FROM smartregression.run_reports WHERE report_id=:id"),
                dict(id=report.payload.report.report_id),
            )
            == 1
        )


def test_restart_is_interrupted_and_preserves_idempotency(runs):
    service, user, _, project, *_ = runs
    run, _ = service.create(user, project, body())
    assert service.store.start(user, project, str(run.id))
    service.store.interrupt()
    assert service.store.get(user, project, str(run.id)).status == "interrupted"
    repeated, created = service.create(user, project, body())
    assert not created and repeated.status == "interrupted"


def test_archived_project_cannot_create_or_start_work(runs):
    service, user, _, project, projects, _ = runs
    run, _ = service.create(user, project, body())
    projects.archive(user, project, 1, True)
    assert not service.store.start(user, project, str(run.id))
    with pytest.raises(AuthFailure, match="project_archived"):
        service.create(user, project, body("new-request-2"))


def test_analysis_error_is_not_completed(runs):
    service, user, _, project, *_ = runs
    run, _ = service.create(user, project, body())

    def broken(_):
        raise ValueError("private input never exposed")

    service.analyze = broken
    service.execute(user, project, str(run.id))
    failed = service.store.get(user, project, str(run.id))
    assert failed.status == "failed" and failed.error_code == "analysis_failed"
    assert not failed.report_available

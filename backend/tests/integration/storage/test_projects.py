"""Real PostgreSQL project isolation, concurrency, and activity invariants."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import text

from smartregression.adapters.storage.project_store import PostgresProjectStore
from smartregression.application.auth import AuthFailure
from smartregression.application.projects import ProjectService
from smartregression.contracts.projects import ProjectCreate, ProjectUpdate


@pytest.fixture
def projects(migrated):
    owner, runtime, _ = migrated
    identities = [str(uuid4()), str(uuid4())]
    with owner.begin() as conn:
        for identity in identities:
            conn.execute(
                text(
                    "INSERT INTO smartregression.web_users "
                    "(id,email,display_name,password_hash,verified) "
                    "VALUES(:id,:email,'Test','unused',true)"
                ),
                dict(id=identity, email=identity + "@example.com"),
            )
    service = ProjectService(PostgresProjectStore(runtime), lambda url: None)
    return service, *identities, owner


def create(service, user, title="Example"):
    return service.create(user, ProjectCreate(title=title, repository_url="https://github.com/a/b"))


def test_project_owner_isolation_and_version_conflicts(projects):
    service, user, stranger, _ = projects
    project = create(service, user)
    assert service.list(stranger).items == []
    for action in (
        lambda: service.get(stranger, str(project.id)),
        lambda: service.update(stranger, str(project.id), ProjectUpdate(title="Other", version=1)),
        lambda: service.archive(stranger, str(project.id), 1, True),
        lambda: service.activity(stranger, str(project.id)),
    ):
        with pytest.raises(AuthFailure) as error:
            action()
        assert error.value.status == 404
    updated = service.update(user, str(project.id), ProjectUpdate(title="Changed", version=1))
    assert updated.version == 2 and updated.title == "Changed"
    with pytest.raises(AuthFailure, match="version_conflict"):
        service.update(user, str(project.id), ProjectUpdate(title="Overwrite", version=1))
    assert service.get(user, str(project.id)).title == "Changed"


def test_archive_restore_and_active_limit(projects):
    service, user, *_ = projects
    items = [create(service, user) for _ in range(3)]
    with pytest.raises(AuthFailure, match="active_project_limit"):
        create(service, user)
    archived = service.archive(user, str(items[0].id), 1, True)
    assert archived.archived and archived.version == 2
    create(service, user)
    with pytest.raises(AuthFailure, match="active_project_limit"):
        service.archive(user, str(archived.id), 2, False)
    assert len(service.list(user).items) == 3
    assert len(service.list(user, archived=True).items) == 1


def test_concurrent_create_never_exceeds_three(projects):
    service, user, *_ = projects
    barrier = Barrier(5)

    def attempt(_):
        barrier.wait(timeout=10)
        try:
            create(service, user)
            return "created"
        except AuthFailure as failure:
            return failure.code

    with ThreadPoolExecutor(max_workers=5) as executor:
        outcomes = list(executor.map(attempt, range(5)))
    assert outcomes.count("created") == 3
    assert outcomes.count("active_project_limit") == 2


def test_pagination_search_and_activity_are_stable(projects):
    service, user, *_ = projects
    first = create(service, user, "Payments")
    create(service, user, "Invoices")
    create(service, user, "Users")
    one = service.list(user, limit=1)
    two = service.list(user, limit=1, cursor=one.next_cursor)
    three = service.list(user, limit=1, cursor=two.next_cursor)
    assert len({one.items[0].id, two.items[0].id, three.items[0].id}) == 3
    assert three.next_cursor is None
    assert service.list(user, search="PAY").items[0].id == first.id
    with pytest.raises(AuthFailure, match="invalid_cursor"):
        service.list(user, cursor="not-a-cursor")
    assert service.activity(user, str(first.id)).items[0].action == "project_created"


def test_transaction_rollback_leaves_no_project_or_activity(projects):
    service, user, _, owner = projects
    identity = str(uuid4())
    with pytest.raises(RuntimeError):
        with service.store.transaction() as tx:
            tx.create(
                user,
                identity,
                ProjectCreate(title="Rollback", repository_url="https://github.com/a/b"),
            )
            tx.activity(user, identity, "project_created", identity)
            raise RuntimeError("rollback")
    with owner.connect() as conn:
        assert (
            conn.scalar(
                text("SELECT count(*) FROM smartregression.web_activity WHERE project_id=:id"),
                dict(id=identity),
            )
            == 0
        )
    with pytest.raises(AuthFailure) as error:
        service.get(user, identity)
    assert error.value.status == 404

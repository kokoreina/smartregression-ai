"""Notes and view state are durable, versioned and isolated per account/project."""

import pytest
from backend.tests.integration.storage.test_explorer import explorer  # noqa: F401
from backend.tests.integration.storage.test_web_runs import runs  # noqa: F401 -- nested fixture
from backend.tests.unit.test_repository_web import TARGET

from smartregression.adapters.storage.note_store import PostgresNoteStore
from smartregression.application.auth import AuthFailure
from smartregression.application.notes import NoteService
from smartregression.contracts.notes import NoteCreate, NoteUpdate, ViewStateInput


def test_notes_anchor_versions_and_cross_owner(request):
    service, user, stranger, project, _ = request.getfixturevalue("explorer")
    service.materialize(user, project, TARGET)
    service = NoteService(PostgresNoteStore(service.store.engine))
    value = service.create(
        user,
        project,
        NoteCreate(commit=TARGET, path="app.py", title="Check entry point", body="Review callers"),
    )
    changed = service.update(
        user, project, str(value.id), NoteUpdate(version=1, title="Updated", body="Keep evidence")
    )
    assert changed.version == 2
    with pytest.raises(AuthFailure, match="version_conflict"):
        service.update(user, project, str(value.id), NoteUpdate(version=1, title="Old edit"))
    with pytest.raises(AuthFailure) as error:
        service.update(
            stranger, project, str(value.id), NoteUpdate(version=2, title="Unauthorized")
        )
    assert error.value.status == 404
    loaded = service.store.list(user, project).items[0]
    assert loaded.body == "Keep evidence" and loaded.stale is False
    service.update(
        user, project, str(value.id), NoteUpdate(version=2, title="Archived", archived=True)
    )
    assert service.store.list(user, project).items == []


def test_view_state_optimistic_conflict_and_owner(request):
    service, user, stranger, project, _ = request.getfixturevalue("explorer")
    service.materialize(user, project, TARGET)
    store = PostgresNoteStore(service.store.engine)
    assert store.view(user, project) is None
    first = store.save_view(
        user, project, ViewStateInput(version=0, commit=TARGET, path="app.py", tab="details")
    )
    assert first.version == 1 and store.view(user, project).path == "app.py"
    with pytest.raises(AuthFailure, match="version_conflict"):
        store.save_view(user, project, ViewStateInput(version=0, commit=TARGET))
    with pytest.raises(AuthFailure) as error:
        store.view(stranger, project)
    assert error.value.status == 404
    second = store.save_view(
        user, project, ViewStateInput(version=1, commit=TARGET, path="deleted.py")
    )
    assert second.version == 2 and store.view(user, project).stale is True

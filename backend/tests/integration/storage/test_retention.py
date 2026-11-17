"""Operator retention removes only expired unreferenced caches, never notes/reports."""

from datetime import UTC, datetime, timedelta

import pytest
from backend.tests.integration.storage.test_explorer import explorer  # noqa: F401
from backend.tests.integration.storage.test_web_runs import runs  # noqa: F401
from sqlalchemy import text

from smartregression.adapters.storage.note_store import PostgresNoteStore
from smartregression.adapters.storage.retention import prune_cache
from smartregression.application.notes import NoteService
from smartregression.contracts.notes import NoteCreate, ViewStateInput


def test_retention_dryrun_expired_cache_and_business_reference(request, migrated):
    service, user, _, project, _ = request.getfixturevalue("explorer")
    owner, _, _ = migrated
    base, target = "a" * 40, "b" * 40
    service.materialize(user, project, base)
    service.materialize(user, project, target)
    notes = NoteService(PostgresNoteStore(service.store.engine))
    notes.create(user, project, NoteCreate(commit=target, path="app.py", title="Keep evidence"))
    notes.store.save_view(user, project, ViewStateInput(version=0, commit=base, path="app.py"))
    old = datetime.now(UTC) - timedelta(days=100)
    with owner.begin() as conn:
        conn.execute(
            text(
                "UPDATE smartregression.web_explorer_snapshots SET created_at=:old "
                "WHERE owner_id=:owner"
            ),
            {"old": old, "owner": user},
        )
        conn.execute(
            text(
                "UPDATE smartregression.web_view_states SET updated_at=:old WHERE owner_id=:owner"
            ),
            {"old": old, "owner": user},
        )
    dry = prune_cache(owner)
    assert dry["snapshots"] >= 1 and dry["view_states"] >= 1
    assert service.read(user, project, base)
    prune_cache(owner, apply=True)
    assert service.read(user, project, target)
    assert len(notes.store.list(user, project).items) == 1
    from smartregression.application.auth import AuthFailure

    with pytest.raises(AuthFailure, match="snapshot_not_ready"):
        service.read(user, project, base)

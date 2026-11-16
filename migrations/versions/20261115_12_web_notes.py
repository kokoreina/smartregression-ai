"""Versioned notes/pins and one resumable view per owned project."""
from alembic import op

revision='20261115_12'
down_revision='20261115_11'
branch_labels=None
depends_on=None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.web_notes (
            id UUID PRIMARY KEY, owner_id UUID NOT NULL,project_id UUID NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('note','pin')),
            commit TEXT NOT NULL CHECK(commit ~ '^[0-9a-f]{40}$'),path TEXT NOT NULL,
            title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
            body TEXT NOT NULL CHECK(length(body)<=10000),
            version INTEGER NOT NULL DEFAULT 1 CHECK(version>0),
            archived BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(owner_id,project_id) REFERENCES smartregression.web_projects(owner_id,id)
                ON UPDATE RESTRICT ON DELETE RESTRICT
        );
        CREATE INDEX ix_web_notes_owner_project_created
            ON smartregression.web_notes(owner_id,project_id,created_at DESC,id DESC);
        CREATE TABLE smartregression.web_view_states (
            owner_id UUID NOT NULL,project_id UUID NOT NULL,
            version INTEGER NOT NULL CHECK(version>0),
            commit TEXT NOT NULL CHECK(commit ~ '^[0-9a-f]{40}$'),path TEXT,
            tab TEXT NOT NULL CHECK(tab IN ('tree','graph','details')),
            expanded_paths JSONB NOT NULL CHECK(jsonb_typeof(expanded_paths)='array'),
            focus_only BOOLEAN NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(owner_id,project_id),
            FOREIGN KEY(owner_id,project_id) REFERENCES smartregression.web_projects(owner_id,id)
                ON UPDATE RESTRICT ON DELETE RESTRICT
        );
        CREATE INDEX ix_web_view_states_updated ON smartregression.web_view_states(updated_at);
    """)


def downgrade():
    raise RuntimeError('forward_only_migration_restore_backup')

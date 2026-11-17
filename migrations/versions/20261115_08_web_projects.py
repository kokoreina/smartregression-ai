"""Personal projects and append-only activity, separate from research storage."""

from alembic import op

revision = "20261115_08"
down_revision = "20261115_07"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.web_projects (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL REFERENCES smartregression.web_users(id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            title TEXT NOT NULL CHECK (length(btrim(title)) BETWEEN 1 AND 120),
            description TEXT NOT NULL DEFAULT '' CHECK (length(description)<=2000),
            repository_url TEXT NOT NULL,
            archived BOOLEAN NOT NULL DEFAULT FALSE,
            version INTEGER NOT NULL DEFAULT 1 CHECK (version>0),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(owner_id,id)
        );
        CREATE INDEX ix_web_projects_owner_created
            ON smartregression.web_projects(owner_id,archived,created_at DESC,id DESC);
        CREATE TABLE smartregression.web_activity (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL,
            project_id UUID NOT NULL,
            action TEXT NOT NULL CHECK (length(action) BETWEEN 1 AND 80),
            object_id TEXT NOT NULL CHECK (length(object_id) BETWEEN 1 AND 128),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(owner_id,project_id) REFERENCES smartregression.web_projects(owner_id,id)
                ON UPDATE RESTRICT ON DELETE RESTRICT
        );
        CREATE INDEX ix_web_activity_owner_project_created
            ON smartregression.web_activity(owner_id,project_id,created_at DESC,id DESC);
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

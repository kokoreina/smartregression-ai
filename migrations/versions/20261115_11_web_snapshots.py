"""Immutable owner/project/SHA/config explorer cache, separate from research manifests."""
from alembic import op

revision='20261115_11'
down_revision='20261115_10'
branch_labels=None
depends_on=None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.web_explorer_snapshots (
            owner_id UUID NOT NULL,
            project_id UUID NOT NULL,
            commit TEXT NOT NULL CHECK(commit ~ '^[0-9a-f]{40}$'),
            config_digest TEXT NOT NULL CHECK(config_digest ~ '^[0-9a-f]{64}$'),
            payload JSONB NOT NULL CHECK(jsonb_typeof(payload)='object'),
            sources JSONB NOT NULL CHECK(jsonb_typeof(sources)='object'),
            payload_digest TEXT NOT NULL CHECK(payload_digest ~ '^[0-9a-f]{64}$'),
            sources_digest TEXT NOT NULL CHECK(sources_digest ~ '^[0-9a-f]{64}$'),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(owner_id,project_id,commit,config_digest),
            FOREIGN KEY(owner_id,project_id) REFERENCES smartregression.web_projects(owner_id,id)
                ON UPDATE RESTRICT ON DELETE RESTRICT
        );
    """)


def downgrade():
    raise RuntimeError('forward_only_migration_restore_backup')

"""Immutable proposed changes; inputs never modify or execute the source repository."""
from alembic import op

revision='20261115_13'
down_revision='20261115_12'
branch_labels=None
depends_on=None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.web_scenarios (
            id UUID PRIMARY KEY,owner_id UUID NOT NULL,project_id UUID NOT NULL,
            baseline TEXT NOT NULL CHECK(baseline ~ '^[0-9a-f]{40}$'),
            config_digest TEXT NOT NULL CHECK(config_digest ~ '^[0-9a-f]{64}$'),
            idempotency_key TEXT NOT NULL,
            input_digest TEXT NOT NULL CHECK(input_digest ~ '^[0-9a-f]{64}$'),
            mode TEXT NOT NULL CHECK(mode IN ('code','diff','description')),
            payload JSONB NOT NULL CHECK(jsonb_typeof(payload)='object'),
            payload_digest TEXT NOT NULL CHECK(payload_digest ~ '^[0-9a-f]{64}$'),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(owner_id,project_id,idempotency_key),
            FOREIGN KEY(owner_id,project_id) REFERENCES smartregression.web_projects(owner_id,id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            FOREIGN KEY(owner_id,project_id,baseline,config_digest)
                REFERENCES smartregression.web_explorer_snapshots(owner_id,project_id,commit,config_digest)
                ON UPDATE RESTRICT ON DELETE RESTRICT
        );
        CREATE INDEX ix_web_scenarios_owner_project_created
            ON smartregression.web_scenarios(owner_id,project_id,created_at DESC,id DESC);
    """)


def downgrade():
    raise RuntimeError('forward_only_migration_restore_backup')

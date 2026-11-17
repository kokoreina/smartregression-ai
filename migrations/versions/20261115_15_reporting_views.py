"""Expiring immutable dashboard snapshots, not a second business history."""

from alembic import op

revision = "20261115_15"
down_revision = "20261115_14"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
      CREATE TABLE smartregression.web_reporting_views (
        id UUID PRIMARY KEY, owner_id UUID NOT NULL REFERENCES smartregression.web_users(id)
          ON UPDATE RESTRICT ON DELETE RESTRICT,
        payload JSONB NOT NULL CHECK(jsonb_typeof(payload)='object'),
        payload_digest TEXT NOT NULL CHECK(payload_digest ~ '^[0-9a-f]{64}$'),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL
      );
      CREATE INDEX ix_web_reporting_views_owner_created
        ON smartregression.web_reporting_views(owner_id,created_at DESC);
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

"""Allow budgeted AI requests on immutable snapshots as well as saved runs."""

from alembic import op

revision = "20261115_14"
down_revision = "20261115_13"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
      ALTER TABLE smartregression.web_ai_requests
        ALTER COLUMN run_id DROP NOT NULL,
        ADD COLUMN scope_key TEXT,
        ADD COLUMN context_hash TEXT,
        ADD COLUMN provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN snapshot_commit TEXT,
        ADD COLUMN snapshot_config TEXT;
      UPDATE smartregression.web_ai_requests SET scope_key='run:'||run_id::text;
      ALTER TABLE smartregression.web_ai_requests ALTER COLUMN scope_key SET NOT NULL;
      ALTER TABLE smartregression.web_ai_requests
        DROP CONSTRAINT web_ai_requests_owner_id_run_id_action_idempotency_key_key,
        ADD UNIQUE(owner_id,project_id,scope_key,action,idempotency_key),
        ADD FOREIGN KEY(owner_id,project_id,snapshot_commit,snapshot_config)
          REFERENCES smartregression.web_explorer_snapshots(owner_id,project_id,commit,config_digest)
          ON UPDATE RESTRICT ON DELETE RESTRICT,
        ADD CHECK((run_id IS NOT NULL AND action='commit' AND scope_key='run:'||run_id::text
                    AND snapshot_commit IS NULL AND snapshot_config IS NULL)
          OR (run_id IS NULL AND action<>'commit' AND snapshot_commit IS NOT NULL
                    AND snapshot_config IS NOT NULL AND context_hash IS NOT NULL)),
        ADD CHECK(context_hash IS NULL OR context_hash ~ '^[0-9a-f]{64}$'),
        ADD CHECK(jsonb_typeof(provenance)='object');
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

"""Explicit campaign grants and conservative AI reservations; old ledgers unchanged."""

from alembic import op

revision = "20261115_10"
down_revision = "20261115_09"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.web_ai_campaigns (
            id TEXT PRIMARY KEY,
            max_calls INTEGER NOT NULL CHECK(max_calls BETWEEN 1 AND 10),
            cap_micro_usd INTEGER NOT NULL CHECK(cap_micro_usd BETWEEN 1 AND 200000)
        );
        CREATE TABLE smartregression.web_ai_grants (
            campaign_id TEXT NOT NULL REFERENCES smartregression.web_ai_campaigns(id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            owner_id UUID NOT NULL REFERENCES smartregression.web_users(id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            max_calls INTEGER NOT NULL CHECK(max_calls BETWEEN 1 AND 10),
            cap_micro_usd INTEGER NOT NULL CHECK(cap_micro_usd BETWEEN 1 AND 200000),
            PRIMARY KEY(campaign_id,owner_id)
        );
        CREATE TABLE smartregression.web_ai_requests (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL,
            project_id UUID NOT NULL,
            run_id UUID NOT NULL,
            campaign_id TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            input_digest TEXT NOT NULL CHECK(input_digest ~ '^[0-9a-f]{64}$'),
            action TEXT NOT NULL CHECK(action IN ('commit','hypothesis','reading_guide','search','file','folder')),
            status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed')),
            reservation_micro_usd INTEGER NOT NULL CHECK(reservation_micro_usd BETWEEN 1 AND 20000),
            actual_micro_usd INTEGER CHECK(actual_micro_usd BETWEEN 0 AND reservation_micro_usd),
            campaign_call INTEGER NOT NULL CHECK(campaign_call BETWEEN 1 AND 10),
            batch INTEGER NOT NULL CHECK(batch BETWEEN 1 AND 2),
            result JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMPTZ,
            UNIQUE(owner_id,run_id,action,idempotency_key),
            UNIQUE(campaign_id,campaign_call),
            FOREIGN KEY(campaign_id,owner_id)
                REFERENCES smartregression.web_ai_grants(campaign_id,owner_id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            FOREIGN KEY(owner_id,project_id,run_id)
                REFERENCES smartregression.web_runs(owner_id,project_id,id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            CHECK ((status IN ('queued','running') AND finished_at IS NULL AND result IS NULL) OR
                (status IN ('completed','failed') AND finished_at IS NOT NULL AND result IS NOT NULL))
        );
        CREATE INDEX ix_web_ai_requests_owner_run ON smartregression.web_ai_requests(owner_id,run_id,created_at DESC);
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

"""Durable product lifecycle linked to immutable research reports."""

from alembic import op

revision = "20261115_09"
down_revision = "20261115_08"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.web_runs (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL,
            project_id UUID NOT NULL,
            repository_url TEXT NOT NULL,
            base TEXT NOT NULL CHECK (base ~ '^[0-9a-f]{40}$'),
            target TEXT NOT NULL CHECK (target ~ '^[0-9a-f]{40}$'),
            config_digest TEXT NOT NULL CHECK (config_digest ~ '^[0-9a-f]{64}$'),
            idempotency_key TEXT NOT NULL,
            request_digest TEXT NOT NULL CHECK (request_digest ~ '^[0-9a-f]{64}$'),
            status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed','interrupted')),
            started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMPTZ,
            error_code TEXT,
            payload JSONB,
            payload_digest TEXT,
            repository_id TEXT,
            analysis_run_id TEXT,
            report_id TEXT,
            ai_status TEXT NOT NULL DEFAULT 'not_run'
                CHECK(ai_status IN ('not_run','running','completed','failed')),
            UNIQUE(owner_id,project_id,idempotency_key),
            UNIQUE(owner_id,project_id,id),
            FOREIGN KEY(owner_id,project_id) REFERENCES smartregression.web_projects(owner_id,id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            FOREIGN KEY(repository_id,analysis_run_id,report_id)
                REFERENCES smartregression.run_reports(repository_id,run_id,report_id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            CHECK ((payload IS NULL AND payload_digest IS NULL AND repository_id IS NULL
                AND analysis_run_id IS NULL AND report_id IS NULL) OR
                (payload IS NOT NULL AND jsonb_typeof(payload)='object'
                AND payload_digest ~ '^[0-9a-f]{64}$' AND repository_id IS NOT NULL
                AND analysis_run_id IS NOT NULL AND report_id IS NOT NULL)),
            CHECK ((status IN ('queued','running') AND finished_at IS NULL) OR
                (status IN ('completed','failed','interrupted') AND finished_at IS NOT NULL)),
            CHECK (status <> 'completed' OR payload IS NOT NULL)
        );
        CREATE UNIQUE INDEX ix_web_runs_active_owner ON smartregression.web_runs(owner_id)
            WHERE status IN ('queued','running');
        CREATE INDEX ix_web_runs_owner_project_started
            ON smartregression.web_runs(owner_id,project_id,started_at DESC,id DESC);
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

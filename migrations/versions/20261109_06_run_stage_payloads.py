"""Immutable core payload fingerprints serialize report/evidence overlap claims."""

from alembic import op

revision = "20261109_06"
down_revision = "20261105_05"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.run_stage_payloads (
            repository_id TEXT NOT NULL, run_id TEXT NOT NULL,
            stage_name TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (repository_id, run_id, stage_name),
            CONSTRAINT fk_stage_payload_run FOREIGN KEY (repository_id, run_id)
                REFERENCES smartregression.analysis_runs(repository_id, run_id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            CONSTRAINT ck_stage_payload_name CHECK
                (stage_name IN ('changes','graph','impact','evidence')),
            CONSTRAINT ck_stage_payload_digest CHECK
                (payload_sha256 ~ '^[0-9a-f]{64}$')
        )
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

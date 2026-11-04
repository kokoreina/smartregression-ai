"""Accepted P3 bounded immutable evidence; additive after inventory."""

from alembic import op

revision = "20261104_04"
down_revision = "20261104_03"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.evidence_bundles (
            repository_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            bundle_format TEXT NOT NULL,
            payload BYTEA NOT NULL,
            payload_sha256 TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (repository_id, run_id),
            CONSTRAINT fk_evidence_run FOREIGN KEY (repository_id, run_id)
                REFERENCES smartregression.analysis_runs(repository_id, run_id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            CONSTRAINT ck_evidence_format CHECK (length(bundle_format) BETWEEN 1 AND 128),
            CONSTRAINT ck_evidence_size CHECK (octet_length(payload) BETWEEN 1 AND 2097152),
            CONSTRAINT ck_evidence_digest CHECK (payload_sha256 ~ '^[0-9a-f]{64}$')
        )
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

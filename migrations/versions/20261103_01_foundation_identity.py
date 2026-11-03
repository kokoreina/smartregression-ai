"""Frozen PostgreSQL DDL for 20261103_01."""

import sqlalchemy as sa
from alembic import op

revision = "20261103_01"
down_revision = None
branch_labels = None
depends_on = None

_DDL = (
    """
    CREATE TABLE smartregression.repositories (
    repository_id TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (repository_id),
    CONSTRAINT ck_repository_id CHECK (repository_id ~
    '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$'),
    CONSTRAINT ck_repository_source_kind CHECK (source_kind IN ('local','github'))
    )
    """,
    """
    CREATE TABLE smartregression.snapshots (
    repository_id TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    manifest_version TEXT NOT NULL,
    materializer_version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (repository_id, commit_sha, snapshot_id),
    CONSTRAINT fk_snapshot_repository FOREIGN KEY(repository_id) REFERENCES
    smartregression.repositories (repository_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_snapshot_commit CHECK (commit_sha ~ '^([0-9a-f]{40}|[0-9a-f]{64})$'),
    CONSTRAINT ck_snapshot_digest CHECK (snapshot_id ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_snapshot_manifest_version CHECK (length(manifest_version) BETWEEN 1 AND
    128),
    CONSTRAINT ck_snapshot_materializer_version CHECK (length(materializer_version) BETWEEN
    1 AND 128)
    )
    """,
    """
    CREATE TABLE smartregression.analysis_runs (
    repository_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    base_sha TEXT NOT NULL,
    target_sha TEXT NOT NULL,
    base_snapshot_id TEXT,
    target_snapshot_id TEXT,
    comparison_mode TEXT NOT NULL,
    data_kind TEXT NOT NULL,
    configuration JSONB NOT NULL,
    configuration_sha256 TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (repository_id, run_id),
    CONSTRAINT fk_run_repository FOREIGN KEY(repository_id) REFERENCES
    smartregression.repositories (repository_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_run_base_snapshot FOREIGN KEY(repository_id, base_sha, base_snapshot_id)
    REFERENCES smartregression.snapshots (repository_id, commit_sha, snapshot_id) ON DELETE
    RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_run_target_snapshot FOREIGN KEY(repository_id, target_sha,
    target_snapshot_id) REFERENCES smartregression.snapshots (repository_id, commit_sha,
    snapshot_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_run_id CHECK (octet_length(run_id) BETWEEN 1 AND 512 AND run_id =
    btrim(run_id)),
    CONSTRAINT ck_run_base_sha CHECK (base_sha ~ '^([0-9a-f]{40}|[0-9a-f]{64})$'),
    CONSTRAINT ck_run_target_sha CHECK (target_sha ~ '^([0-9a-f]{40}|[0-9a-f]{64})$'),
    CONSTRAINT ck_run_base_digest CHECK (base_snapshot_id IS NULL OR base_snapshot_id ~
    '^[0-9a-f]{64}$'),
    CONSTRAINT ck_run_target_digest CHECK (target_snapshot_id IS NULL OR target_snapshot_id
    ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_run_same_commit CHECK (base_sha <> target_sha OR base_snapshot_id IS NULL
    OR target_snapshot_id IS NULL OR base_snapshot_id = target_snapshot_id),
    CONSTRAINT ck_run_comparison CHECK (comparison_mode = 'direct_two_tree'),
    CONSTRAINT ck_run_data_kind CHECK (data_kind IN ('demo','real')),
    CONSTRAINT ck_run_configuration CHECK (jsonb_typeof(configuration) = 'object'),
    CONSTRAINT ck_run_configuration_digest CHECK (configuration_sha256 ~ '^[0-9a-f]{64}$')
    )
    """,
)


def upgrade():
    for statement in _DDL:
        op.execute(sa.text(statement))


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

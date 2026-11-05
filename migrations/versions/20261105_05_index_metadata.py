"""P5 scoped lexical index/chunk metadata; source bytes stay in local artifacts."""

from alembic import op

revision = "20261105_05"
down_revision = "20261104_04"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.knowledge_indexes (
            repository_id TEXT NOT NULL, commit_sha TEXT NOT NULL,
            snapshot_id TEXT NOT NULL, index_version TEXT NOT NULL,
            configuration_sha256 TEXT NOT NULL, index_id TEXT NOT NULL,
            backend TEXT NOT NULL, embedding_model TEXT, record JSONB NOT NULL,
            state TEXT NOT NULL, attempt_id TEXT NOT NULL, error_code TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (repository_id,commit_sha,snapshot_id,index_version,configuration_sha256),
            CONSTRAINT uq_knowledge_index_identity UNIQUE (repository_id,index_id),
            CONSTRAINT fk_knowledge_index_snapshot
                FOREIGN KEY (repository_id,commit_sha,snapshot_id)
                REFERENCES smartregression.snapshots(repository_id,commit_sha,snapshot_id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            CONSTRAINT ck_knowledge_index_digests CHECK
                (index_id ~ '^[0-9a-f]{64}$' AND configuration_sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_knowledge_index_version CHECK
                (index_version ~ '^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$'),
            CONSTRAINT ck_knowledge_index_backend CHECK
                (backend = 'local-lexical' AND embedding_model IS NULL),
            CONSTRAINT ck_knowledge_index_record CHECK
                (jsonb_typeof(record) = 'object' AND octet_length(record::text) <= 4194304),
            CONSTRAINT ck_knowledge_index_attempt CHECK (attempt_id ~ '^[a-f0-9]{32}$'),
            CONSTRAINT ck_knowledge_index_state CHECK
                (state IN ('building','ready','failed') AND ((state = 'failed'
                AND error_code IS NOT NULL AND error_code ~ '^[a-z][a-z0-9_]{0,127}$')
                OR (state <> 'failed' AND error_code IS NULL)))
        )
    """)
    op.execute("""
        CREATE TABLE smartregression.index_chunks (
            repository_id TEXT NOT NULL, index_id TEXT NOT NULL, chunk_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL, path TEXT NOT NULL, line_start INTEGER NOT NULL,
            line_end INTEGER NOT NULL, content_sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL,
            PRIMARY KEY (repository_id,index_id,chunk_id),
            CONSTRAINT uq_index_chunk_ordinal UNIQUE (repository_id,index_id,ordinal),
            CONSTRAINT fk_index_chunk_index FOREIGN KEY (repository_id,index_id)
                REFERENCES smartregression.knowledge_indexes(repository_id,index_id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            CONSTRAINT ck_index_chunk_hashes CHECK
                (chunk_id ~ '^[0-9a-f]{64}$' AND content_sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_index_chunk_ordinal CHECK (ordinal BETWEEN 0 AND 9999),
            CONSTRAINT ck_index_chunk_range CHECK
                (line_start > 0 AND line_end >= line_start AND line_end-line_start < 128),
            CONSTRAINT ck_index_chunk_size CHECK (size_bytes BETWEEN 1 AND 8192),
            CONSTRAINT ck_index_chunk_path CHECK (octet_length(path) BETWEEN 1 AND 4096)
        )
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

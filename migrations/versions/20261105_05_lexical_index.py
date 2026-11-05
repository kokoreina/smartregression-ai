"""P5 lexical metadata; user explicitly authorized missing H2/KH dependency implementation."""

from alembic import op

revision = "20261105_05"
down_revision = "20261104_04"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.knowledge_indexes (
            repository_id TEXT NOT NULL,
            index_id TEXT NOT NULL,
            commit_sha TEXT NOT NULL,
            snapshot_id TEXT NOT NULL,
            configuration_id TEXT NOT NULL,
            configuration JSONB NOT NULL,
            index_version TEXT NOT NULL,
            backend_kind TEXT NOT NULL,
            embedding_model TEXT NULL,
            state TEXT NOT NULL,
            attempt_id TEXT NOT NULL,
            error_code TEXT NULL,
            manifest_key TEXT NOT NULL,
            manifest_sha256 TEXT NOT NULL,
            manifest_bytes BIGINT NOT NULL,
            chunk_count INTEGER NOT NULL,
            content_bytes BIGINT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY(repository_id,index_id),
            CONSTRAINT fk_index_snapshot FOREIGN KEY(repository_id,commit_sha,snapshot_id)
                REFERENCES smartregression.snapshots(repository_id,commit_sha,snapshot_id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            CONSTRAINT uq_index_configuration_scope UNIQUE(repository_id,commit_sha,snapshot_id,
                configuration_id,index_version),
            CONSTRAINT ck_index_ids CHECK(index_id ~ '^[0-9a-f]{64}$'
                AND configuration_id ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_index_backend CHECK(backend_kind='lexical' AND embedding_model IS NULL),
            CONSTRAINT ck_index_state CHECK(state IN ('building','ready','failed')),
            CONSTRAINT ck_index_attempt CHECK(attempt_id ~ '^[0-9a-f]{32}$'),
            CONSTRAINT ck_index_error CHECK((state='failed')=(error_code IS NOT NULL)),
            CONSTRAINT ck_index_manifest_digest CHECK(manifest_sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_index_manifest_size CHECK(manifest_bytes BETWEEN 1 AND 16777216),
            CONSTRAINT ck_index_bounds CHECK(chunk_count BETWEEN 0 AND 10000
                AND content_bytes BETWEEN 0 AND 33554432),
            CONSTRAINT ck_index_configuration CHECK(jsonb_typeof(configuration)='object')
        )
    """)
    op.execute("""
        CREATE TABLE smartregression.knowledge_chunks (
            repository_id TEXT NOT NULL,
            index_id TEXT NOT NULL,
            chunk_id TEXT NOT NULL,
            path TEXT NOT NULL,
            line_start INTEGER NOT NULL,
            line_end INTEGER NOT NULL,
            symbol TEXT NULL,
            content_sha256 TEXT NOT NULL,
            content_key TEXT NOT NULL,
            content_bytes INTEGER NOT NULL,
            PRIMARY KEY(repository_id,index_id,chunk_id),
            CONSTRAINT fk_chunk_index FOREIGN KEY(repository_id,index_id)
                REFERENCES smartregression.knowledge_indexes(repository_id,index_id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            CONSTRAINT ck_chunk_digests CHECK(chunk_id ~ '^[0-9a-f]{64}$'
                AND content_sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_chunk_range CHECK(line_start>0 AND line_end>=line_start
                AND line_end-line_start<128),
            CONSTRAINT ck_chunk_size CHECK(content_bytes BETWEEN 1 AND 8192)
        )
    """)
    op.execute("""
        CREATE FUNCTION smartregression.guard_index_transition() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.state='ready'
                OR (OLD.state='building' AND NEW.attempt_id<>OLD.attempt_id)
                OR (OLD.state='failed' AND NEW.state<>'building') THEN
                RAISE EXCEPTION 'invalid_index_transition';
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER index_transition BEFORE UPDATE ON smartregression.knowledge_indexes
        FOR EACH ROW EXECUTE FUNCTION smartregression.guard_index_transition()
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

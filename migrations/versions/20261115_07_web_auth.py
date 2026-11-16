"""Add account data without changing research reports or inventory semantics."""

from alembic import op

revision = "20261115_07"
down_revision = "20261109_06"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE smartregression.web_users (
            id UUID PRIMARY KEY,
            email TEXT UNIQUE NOT NULL CHECK (email = lower(btrim(email))),
            display_name TEXT NOT NULL CHECK (length(display_name) BETWEEN 1 AND 80),
            password_hash TEXT NOT NULL,
            verified BOOLEAN NOT NULL DEFAULT FALSE,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE smartregression.web_sessions (
            digest TEXT PRIMARY KEY CHECK (digest ~ '^[0-9a-f]{64}$'),
            user_id UUID NOT NULL REFERENCES smartregression.web_users(id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked_at TIMESTAMPTZ,
            CHECK (expires_at > created_at)
        );
        CREATE INDEX ix_web_sessions_user ON smartregression.web_sessions(user_id);
        CREATE TABLE smartregression.web_account_tokens (
            digest TEXT PRIMARY KEY CHECK (digest ~ '^[0-9a-f]{64}$'),
            user_id UUID NOT NULL REFERENCES smartregression.web_users(id)
                ON UPDATE RESTRICT ON DELETE RESTRICT,
            purpose TEXT NOT NULL CHECK (purpose IN ('verify', 'reset')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ,
            CHECK (expires_at > created_at)
        );
        CREATE INDEX ix_web_account_tokens_user ON smartregression.web_account_tokens(user_id);
        CREATE TABLE smartregression.web_rate_limits (
            key_hash TEXT NOT NULL CHECK (key_hash ~ '^[0-9a-f]{64}$'),
            window_start TIMESTAMPTZ NOT NULL,
            attempts INTEGER NOT NULL CHECK (attempts > 0),
            PRIMARY KEY (key_hash, window_start)
        );
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")

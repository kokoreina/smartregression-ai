"""Auth metadata for migration drift checks, without creating database objects."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


def add_auth_tables(metadata):
    sa.Table(
        "web_users",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column("email", sa.Text, unique=True, nullable=False),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("email = lower(btrim(email))"),
        sa.CheckConstraint("length(display_name) BETWEEN 1 AND 80"),
    )
    for name, index in [
        ("web_sessions", "ix_web_sessions_user"),
        ("web_account_tokens", "ix_web_account_tokens_user"),
    ]:
        columns = [
            sa.Column("digest", sa.Text, primary_key=True),
            sa.Column(
                "user_id",
                UUID,
                sa.ForeignKey(
                    "smartregression.web_users.id", ondelete="RESTRICT", onupdate="RESTRICT"
                ),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("digest ~ '^[0-9a-f]{64}$'"),
            sa.CheckConstraint("expires_at > created_at"),
        ]
        if name == "web_sessions":
            columns.append(sa.Column("revoked_at", sa.DateTime(timezone=True)))
        else:
            columns.extend(
                [
                    sa.Column("purpose", sa.Text, nullable=False),
                    sa.Column("used_at", sa.DateTime(timezone=True)),
                    sa.CheckConstraint("purpose IN ('verify', 'reset')"),
                ]
            )
        table = sa.Table(name, metadata, *columns)
        sa.Index(index, table.c.user_id)
    sa.Table(
        "web_rate_limits",
        metadata,
        sa.Column("key_hash", sa.Text, primary_key=True),
        sa.Column("window_start", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.CheckConstraint("key_hash ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("attempts > 0"),
    )

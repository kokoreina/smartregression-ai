"""Metadata for owner-scoped dashboard snapshot cache."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def add_reporting_tables(metadata):
    table = sa.Table(
        "web_reporting_views",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "owner_id",
            UUID,
            sa.ForeignKey("smartregression.web_users.id", onupdate="RESTRICT", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("payload_digest", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("jsonb_typeof(payload)='object'"),
        sa.CheckConstraint("payload_digest ~ '^[0-9a-f]{64}$'"),
    )
    sa.Index("ix_web_reporting_views_owner_created", table.c.owner_id, table.c.created_at.desc())

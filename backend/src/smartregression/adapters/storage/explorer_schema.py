"""Explorer cache metadata counterpart of frozen migration."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def add_explorer_tables(metadata):
    sa.Table(
        "web_explorer_snapshots",
        metadata,
        sa.Column("owner_id", UUID, primary_key=True),
        sa.Column("project_id", UUID, primary_key=True),
        sa.Column("commit", sa.Text, primary_key=True),
        sa.Column("config_digest", sa.Text, primary_key=True),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("sources", JSONB, nullable=False),
        sa.Column("payload_digest", sa.Text, nullable=False),
        sa.Column("sources_digest", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id"],
            ["smartregression.web_projects.owner_id", "smartregression.web_projects.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint("commit ~ '^[0-9a-f]{40}$'"),
        sa.CheckConstraint("config_digest ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("payload_digest ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("sources_digest ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("jsonb_typeof(payload)='object'"),
        sa.CheckConstraint("jsonb_typeof(sources)='object'"),
    )

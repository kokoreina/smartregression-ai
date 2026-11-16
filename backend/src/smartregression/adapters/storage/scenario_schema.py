"""Metadata for immutable scenario records."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def add_scenario_tables(metadata):
    table = sa.Table(
        "web_scenarios",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("project_id", UUID, nullable=False),
        *[
            sa.Column(k, sa.Text, nullable=False)
            for k in [
                "baseline",
                "config_digest",
                "idempotency_key",
                "input_digest",
                "mode",
                "payload_digest",
            ]
        ],
        sa.Column("payload", JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("owner_id", "project_id", "idempotency_key"),
        sa.CheckConstraint("baseline ~ '^[0-9a-f]{40}$'"),
        sa.CheckConstraint("config_digest ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("input_digest ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("payload_digest ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("mode IN ('code','diff','description')"),
        sa.CheckConstraint("jsonb_typeof(payload)='object'"),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id"],
            ["smartregression.web_projects.owner_id", "smartregression.web_projects.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id", "baseline", "config_digest"],
            [
                "smartregression.web_explorer_snapshots.owner_id",
                "smartregression.web_explorer_snapshots.project_id",
                "smartregression.web_explorer_snapshots.commit",
                "smartregression.web_explorer_snapshots.config_digest",
            ],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )
    sa.Index(
        "ix_web_scenarios_owner_project_created",
        table.c.owner_id,
        table.c.project_id,
        table.c.created_at.desc(),
        table.c.id.desc(),
    )

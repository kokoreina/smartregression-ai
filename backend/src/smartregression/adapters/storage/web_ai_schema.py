"""Metadata for explicit account grants and append-only AI attempts."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def add_web_ai_tables(metadata):
    sa.Table(
        "web_ai_campaigns",
        metadata,
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("max_calls", sa.Integer, nullable=False),
        sa.Column("cap_micro_usd", sa.Integer, nullable=False),
        sa.CheckConstraint("max_calls BETWEEN 1 AND 10"),
        sa.CheckConstraint("cap_micro_usd BETWEEN 1 AND 200000"),
    )
    sa.Table(
        "web_ai_grants",
        metadata,
        sa.Column(
            "campaign_id",
            sa.Text,
            sa.ForeignKey(
                "smartregression.web_ai_campaigns.id", onupdate="RESTRICT", ondelete="RESTRICT"
            ),
            primary_key=True,
        ),
        sa.Column(
            "owner_id",
            UUID,
            sa.ForeignKey("smartregression.web_users.id", onupdate="RESTRICT", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("max_calls", sa.Integer, nullable=False),
        sa.Column("cap_micro_usd", sa.Integer, nullable=False),
        sa.CheckConstraint("max_calls BETWEEN 1 AND 10"),
        sa.CheckConstraint("cap_micro_usd BETWEEN 1 AND 200000"),
    )
    requests = sa.Table(
        "web_ai_requests",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        *[sa.Column(k, UUID, nullable=False) for k in ("owner_id", "project_id")],
        sa.Column("run_id", UUID),
        sa.Column("scope_key", sa.Text, nullable=False),
        sa.Column("context_hash", sa.Text),
        sa.Column("snapshot_commit", sa.Text),
        sa.Column("snapshot_config", sa.Text),
        sa.Column("provenance", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        *[
            sa.Column(k, sa.Text, nullable=False)
            for k in ("campaign_id", "idempotency_key", "input_digest", "action", "status")
        ],
        sa.Column("reservation_micro_usd", sa.Integer, nullable=False),
        sa.Column("actual_micro_usd", sa.Integer),
        sa.Column("campaign_call", sa.Integer, nullable=False),
        sa.Column("batch", sa.Integer, nullable=False),
        sa.Column("result", JSONB),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("owner_id", "project_id", "scope_key", "action", "idempotency_key"),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id", "snapshot_commit", "snapshot_config"],
            [
                "smartregression.web_explorer_snapshots.owner_id",
                "smartregression.web_explorer_snapshots.project_id",
                "smartregression.web_explorer_snapshots.commit",
                "smartregression.web_explorer_snapshots.config_digest",
            ],
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "(run_id IS NOT NULL AND action='commit' AND scope_key='run:'||run_id::text "
            "AND snapshot_commit IS NULL AND snapshot_config IS NULL) OR "
            "(run_id IS NULL AND action<>'commit' AND snapshot_commit IS NOT NULL "
            "AND snapshot_config IS NOT NULL AND context_hash IS NOT NULL)"
        ),
        sa.CheckConstraint("context_hash IS NULL OR context_hash ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("jsonb_typeof(provenance)='object'"),
        sa.UniqueConstraint("campaign_id", "campaign_call"),
        sa.ForeignKeyConstraint(
            ["campaign_id", "owner_id"],
            ["smartregression.web_ai_grants.campaign_id", "smartregression.web_ai_grants.owner_id"],
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id", "run_id"],
            [
                "smartregression.web_runs.owner_id",
                "smartregression.web_runs.project_id",
                "smartregression.web_runs.id",
            ],
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("input_digest ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint(
            "action IN ('commit','hypothesis','reading_guide','search','file','folder',"
            "'overview','chat','changes')",
            name="ck_web_ai_assistant_actions",
        ),
        sa.CheckConstraint("status IN ('queued','running','completed','failed')"),
        sa.CheckConstraint("reservation_micro_usd BETWEEN 1 AND 20000"),
        sa.CheckConstraint("actual_micro_usd BETWEEN 0 AND reservation_micro_usd"),
        sa.CheckConstraint("campaign_call BETWEEN 1 AND 10"),
        sa.CheckConstraint("batch BETWEEN 1 AND 2"),
        sa.CheckConstraint(
            "(status IN ('queued','running') AND finished_at IS NULL AND "
            "result IS NULL) OR (status IN ('completed','failed') AND fin"
            "ished_at IS NOT NULL AND result IS NOT NULL)"
        ),
    )
    sa.Index(
        "ix_web_ai_requests_owner_run",
        requests.c.owner_id,
        requests.c.run_id,
        requests.c.created_at.desc(),
    )

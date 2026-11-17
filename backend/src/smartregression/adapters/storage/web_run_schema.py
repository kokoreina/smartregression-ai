"""Metadata counterpart of durable run migration; never creates tables on import."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def add_web_run_tables(metadata):
    table = sa.Table(
        "web_runs",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("project_id", UUID, nullable=False),
        *[
            sa.Column(name, sa.Text, nullable=False)
            for name in (
                "repository_url",
                "base",
                "target",
                "config_digest",
                "idempotency_key",
                "request_digest",
                "status",
            )
        ],
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.Text),
        sa.Column("payload", JSONB),
        *[
            sa.Column(name, sa.Text)
            for name in ("payload_digest", "repository_id", "analysis_run_id", "report_id")
        ],
        sa.Column("ai_status", sa.Text, nullable=False, server_default=sa.text("'not_run'")),
        sa.UniqueConstraint("owner_id", "project_id", "idempotency_key"),
        sa.UniqueConstraint("owner_id", "project_id", "id"),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id"],
            ["smartregression.web_projects.owner_id", "smartregression.web_projects.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["repository_id", "analysis_run_id", "report_id"],
            [
                "smartregression.run_reports.repository_id",
                "smartregression.run_reports.run_id",
                "smartregression.run_reports.report_id",
            ],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint("base ~ '^[0-9a-f]{40}$'"),
        sa.CheckConstraint("target ~ '^[0-9a-f]{40}$'"),
        sa.CheckConstraint("config_digest ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("request_digest ~ '^[0-9a-f]{64}$'"),
        sa.CheckConstraint("status IN ('queued','running','completed','failed','interrupted')"),
        sa.CheckConstraint("ai_status IN ('not_run','running','completed','failed')"),
        sa.CheckConstraint(
            "(payload IS NULL AND payload_digest IS NULL AND repository_id IS "
            "NULL AND analysis_run_id IS NULL AND report_id IS NULL) OR (paylo"
            "ad IS NOT NULL AND jsonb_typeof(payload)='object' AND payload_dig"
            "est ~ '^[0-9a-f]{64}$' AND repository_id IS NOT NULL AND analysis"
            "_run_id IS NOT NULL AND report_id IS NOT NULL)"
        ),
        sa.CheckConstraint(
            "(status IN ('queued','running') AND finished_at IS NULL) OR (stat"
            "us IN ('completed','failed','interrupted') AND finished_at IS NOT"
            " NULL)"
        ),
        sa.CheckConstraint("status <> 'completed' OR payload IS NOT NULL"),
    )
    sa.Index(
        "ix_web_runs_active_owner",
        table.c.owner_id,
        unique=True,
        postgresql_where=sa.text("status IN ('queued','running')"),
    )
    sa.Index(
        "ix_web_runs_owner_project_started",
        table.c.owner_id,
        table.c.project_id,
        table.c.started_at.desc(),
        table.c.id.desc(),
    )

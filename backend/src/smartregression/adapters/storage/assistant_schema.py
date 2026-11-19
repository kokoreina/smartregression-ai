"""Conversation references, coalesced watch queue and immutable change reports."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def add_assistant_tables(metadata):
    def project_fk():
        return sa.ForeignKeyConstraint(
            ["owner_id", "project_id"],
            ["smartregression.web_projects.owner_id", "smartregression.web_projects.id"],
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        )

    def created():
        return sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )

    threads = sa.Table(
        "web_assistant_threads",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("commit", sa.Text, nullable=False),
        sa.Column("config_digest", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("idempotency_key", sa.Text, nullable=False),
        sa.Column("input_digest", sa.Text, nullable=False),
        created(),
        project_fk(),
        sa.UniqueConstraint("owner_id", "project_id", "id"),
        sa.UniqueConstraint("owner_id", "project_id", "idempotency_key"),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id", "commit", "config_digest"],
            [
                "smartregression.web_explorer_snapshots.owner_id",
                "smartregression.web_explorer_snapshots.project_id",
                "smartregression.web_explorer_snapshots.commit",
                "smartregression.web_explorer_snapshots.config_digest",
            ],
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("length(title) BETWEEN 1 AND 120"),
    )
    sa.Index(
        "ix_assistant_threads_project",
        threads.c.owner_id,
        threads.c.project_id,
        threads.c.created_at.desc(),
    )
    messages = sa.Table(
        "web_assistant_messages",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("thread_id", UUID, nullable=False),
        sa.Column("idempotency_key", sa.Text, nullable=False),
        sa.Column("input_digest", sa.Text, nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("reply", JSONB, nullable=False),
        sa.Column("reply_digest", sa.Text, nullable=False),
        sa.Column(
            "ai_id",
            UUID,
            sa.ForeignKey(
                "smartregression.web_ai_requests.id", ondelete="RESTRICT", onupdate="RESTRICT"
            ),
        ),
        created(),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id", "thread_id"],
            [
                "smartregression.web_assistant_threads.owner_id",
                "smartregression.web_assistant_threads.project_id",
                "smartregression.web_assistant_threads.id",
            ],
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("owner_id", "project_id", "thread_id", "idempotency_key"),
        sa.CheckConstraint("length(question) BETWEEN 1 AND 600"),
        sa.CheckConstraint("jsonb_typeof(reply)='object' AND octet_length(reply::text)<=131072"),
    )
    sa.Index("ix_assistant_messages_thread", messages.c.thread_id, messages.c.created_at)
    sa.Table(
        "web_repo_watches",
        metadata,
        sa.Column("owner_id", UUID, primary_key=True),
        sa.Column("project_id", UUID, primary_key=True),
        sa.Column("branch", sa.Text, nullable=False),
        sa.Column("paths", JSONB, nullable=False),
        sa.Column("automatic", sa.Boolean, nullable=False),
        sa.Column("interval_seconds", sa.Integer, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("last_commit", sa.Text, nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True)),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pending", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("lease_token", UUID),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.Text),
        project_fk(),
        sa.CheckConstraint("jsonb_typeof(paths)='array' AND jsonb_array_length(paths)<=20"),
        sa.CheckConstraint("interval_seconds BETWEEN 300 AND 86400 AND version>0"),
        sa.CheckConstraint("last_commit ~ '^[0-9a-f]{40}$'"),
    )
    notes = sa.Table(
        "web_change_notifications",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("report", JSONB, nullable=False),
        sa.Column("report_digest", sa.Text, nullable=False),
        sa.Column("identity_digest", sa.Text, nullable=False),
        created(),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        project_fk(),
        sa.UniqueConstraint("owner_id", "project_id", "identity_digest"),
        sa.CheckConstraint("jsonb_typeof(report)='object' AND octet_length(report::text)<=1048576"),
    )
    sa.Index(
        "ix_change_notifications_project",
        notes.c.owner_id,
        notes.c.project_id,
        notes.c.created_at.desc(),
    )
    sa.Table(
        "web_github_deliveries",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column("payload_digest", sa.Text, nullable=False),
        sa.Column("repository", sa.Text, nullable=False),
        sa.Column("event", sa.Text, nullable=False),
        sa.Column("branch", sa.Text, nullable=False),
        sa.Column("actor", sa.Text),
        created(),
        sa.CheckConstraint("length(repository)<=140 AND length(event)<=40 AND length(branch)<=200"),
    )

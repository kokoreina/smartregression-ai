"""Metadata counterpart of note/view migration."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def add_note_tables(metadata):
    notes = sa.Table(
        "web_notes",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("project_id", UUID, nullable=False),
        *[
            sa.Column(k, sa.Text, nullable=False)
            for k in ["kind", "commit", "path", "title", "body"]
        ],
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("archived", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("kind IN ('note','pin')"),
        sa.CheckConstraint("commit ~ '^[0-9a-f]{40}$'"),
        sa.CheckConstraint("length(title) BETWEEN 1 AND 120"),
        sa.CheckConstraint("length(body)<=10000"),
        sa.CheckConstraint("version>0"),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id"],
            ["smartregression.web_projects.owner_id", "smartregression.web_projects.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )
    sa.Index(
        "ix_web_notes_owner_project_created",
        notes.c.owner_id,
        notes.c.project_id,
        notes.c.created_at.desc(),
        notes.c.id.desc(),
    )
    state = sa.Table(
        "web_view_states",
        metadata,
        sa.Column("owner_id", UUID, primary_key=True),
        sa.Column("project_id", UUID, primary_key=True),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("commit", sa.Text, nullable=False),
        sa.Column("path", sa.Text),
        sa.Column("tab", sa.Text, nullable=False),
        sa.Column("expanded_paths", JSONB, nullable=False),
        sa.Column("focus_only", sa.Boolean, nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("version>0"),
        sa.CheckConstraint("commit ~ '^[0-9a-f]{40}$'"),
        sa.CheckConstraint("tab IN ('tree','graph','details')"),
        sa.CheckConstraint("jsonb_typeof(expanded_paths)='array'"),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id"],
            ["smartregression.web_projects.owner_id", "smartregression.web_projects.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )
    sa.Index("ix_web_view_states_updated", state.c.updated_at)

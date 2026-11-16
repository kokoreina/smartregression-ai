"""Metadata counterpart of frozen personal-project migration."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


def add_project_tables(metadata):
    def created(name="created_at"):
        return sa.Column(
            name,
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )

    projects = sa.Table(
        "web_projects",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "owner_id",
            UUID,
            sa.ForeignKey("smartregression.web_users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=sa.text("''")),
        sa.Column("repository_url", sa.Text, nullable=False),
        sa.Column("archived", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        created(),
        created("updated_at"),
        sa.CheckConstraint("length(btrim(title)) BETWEEN 1 AND 120"),
        sa.CheckConstraint("length(description)<=2000"),
        sa.CheckConstraint("version>0"),
        sa.UniqueConstraint("owner_id", "id"),
    )
    sa.Index(
        "ix_web_projects_owner_created",
        projects.c.owner_id,
        projects.c.archived,
        projects.c.created_at.desc(),
        projects.c.id.desc(),
    )
    activity = sa.Table(
        "web_activity",
        metadata,
        sa.Column("id", UUID, primary_key=True),
        sa.Column("owner_id", UUID, nullable=False),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("object_id", sa.Text, nullable=False),
        created(),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_id"],
            ["smartregression.web_projects.owner_id", "smartregression.web_projects.id"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint("length(action) BETWEEN 1 AND 80"),
        sa.CheckConstraint("length(object_id) BETWEEN 1 AND 128"),
    )
    sa.Index(
        "ix_web_activity_owner_project_created",
        activity.c.owner_id,
        activity.c.project_id,
        activity.c.created_at.desc(),
        activity.c.id.desc(),
    )

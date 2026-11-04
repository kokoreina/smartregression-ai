"""Explicit operator migrations, never application startup. No DSN in ini/logs."""

import sqlalchemy as sa
from alembic import context

from smartregression.adapters.storage.config import load_database_settings
from smartregression.adapters.storage.connection import database_engine
from smartregression.adapters.storage.schema import SCHEMA, metadata


def migrate(connection):
    context.configure(
        connection=connection,
        target_metadata=metadata,
        include_schemas=True,
        version_table_schema=SCHEMA,
        transactional_ddl=True,
    )
    with context.begin_transaction():
        connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS smartregression"))
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        dialect_name="postgresql",
        target_metadata=metadata,
        literal_binds=True,
        version_table_schema=SCHEMA,
        transactional_ddl=True,
    )
    with context.begin_transaction():
        context.execute("CREATE SCHEMA IF NOT EXISTS smartregression")
        context.run_migrations()
elif context.config.attributes.get("connection") is not None:
    migrate(context.config.attributes["connection"])
else:
    # Plaintext test settings may be passed explicitly by the scoped test harness;
    # normal Alembic commands use H1's remote verify-full policy by default.
    settings = context.config.attributes.get("migration_settings")
    if settings is None:
        settings = load_database_settings(migration=True)
    with database_engine(settings) as engine, engine.connect() as connection:
        migrate(connection)

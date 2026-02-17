"""
Alembic environment configuration for async SQLAlchemy migrations.

Key setup:
- Reads DATABASE_URL from app.config.settings (shares .env with FastAPI)
- Imports all models via app.models so autogenerate can diff them
- Uses asyncpg for async migrations (matches our FastAPI setup)
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import our app's settings and models
# ---------------------------------------------------------------------------

from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402

# Import all models so Base.metadata is fully populated
import app.models  # noqa: E402, F401

# Override sqlalchemy.url from our .env-powered settings
# This avoids hardcoding credentials in alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Point Alembic's autogenerate at our model metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for reviewing migration SQL before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

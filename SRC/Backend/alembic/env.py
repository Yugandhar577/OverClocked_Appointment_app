"""
Backend documentation for `alembic/env.py`.

This migration module documents schema evolution and must stay backward-compatible with existing deployed data.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from SRC.Backend.config import get_settings
from SRC.Backend.db.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
target_metadata = Base.metadata


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# Function explanation:
# `run_migrations_offline` configures Alembic to emit SQL migration
# statements without connecting to the DB. This is useful for generating
# SQL scripts for review or for environments where direct DB access is
# restricted.
#
# Alternative (commented): prefer running migrations online against a
# test/staging database for full-schema validation before applying to prod.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


# Function explanation:
# `do_run_migrations` runs the migration operations using an active
# database connection. It's used by the async runner to apply Alembic
# scripts within a transactional context.
#
# Alternative (commented): use alembic command-line `upgrade head` in a
# deployment pipeline rather than manually invoking the API from Python.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


# Function explanation:
# `run_async_migrations` creates an async SQLAlchemy engine and runs the
# migrations inside an async connection, then disposes the engine. This
# enables performing migrations in async application environments.
#
# Alternative (commented): use a sync engine for migrations when async
# DB drivers are not available or in CI where simpler sync execution is
# preferred.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def run_migrations_online() -> None:
    import asyncio

    asyncio.run(run_async_migrations())


# Function explanation:
# `run_migrations_online` is the entry point for applying migrations in
# a live environment; it delegates to the async runner for actual work.
#
# Alternative (commented): call `run_async_migrations` directly in an
# async-capable process or use Alembic CLI tooling as part of deployment.


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

"""
Performance strategy: PostgreSQL template databases.
- Session-scoped: migrate once into a template DB
- Per-test: CREATE DATABASE ... TEMPLATE ... (fast file-level copy), DROP after
- pytest-xdist: each worker gets its own template DB (no cross-worker coordination)
"""

import asyncio
import os
import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

import alembic.command
import alembic.config


def _admin_url(url: sa.URL) -> sa.URL:
    return url.set(database="postgres")


def _build_url(url: sa.URL, db_name: str) -> sa.URL:
    return url.set(database=db_name)


def _template_db_name(base_db_name: str) -> str:
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    suffix = f"_{worker_id}" if worker_id else ""
    return f"{base_db_name}_template{suffix}"


async def setup_template_database(base_db_url: str) -> str:
    """
    Drop, recreate, and migrate the template database. Returns its name.
    Each xdist worker operates on its own template — no cross-worker locking needed.
    """
    url = sa.make_url(base_db_url)
    assert url.database
    template_db_name = _template_db_name(url.database)
    admin_url = _admin_url(url)
    template_db_url = _build_url(url, template_db_name)

    engine = create_async_engine(
        admin_url, poolclass=NullPool, isolation_level="AUTOCOMMIT"
    )
    async with engine.connect() as conn:
        await conn.execute(sa.text(f"DROP DATABASE IF EXISTS {template_db_name}"))
        await conn.execute(sa.text(f"CREATE DATABASE {template_db_name}"))
    await engine.dispose()

    alembic_cfg = alembic.config.Config("alembic.ini")
    alembic_cfg.set_main_option(
        "sqlalchemy.url", template_db_url.render_as_string(hide_password=False)
    )
    alembic_cfg.set_main_option("{{cookiecutter.__project_slug}}.skip_logging_setup", "true")
    await asyncio.to_thread(alembic.command.upgrade, alembic_cfg, "head")

    return template_db_name


async def create_test_database_from_template(
    base_db_url: str, template_db_name: str
) -> str:
    """
    Create a fresh test database from the template. Returns the new database URL.
    """
    url = sa.make_url(base_db_url)
    test_db_name = f"test_{uuid.uuid4().hex}"
    admin_url = _admin_url(url)

    engine = create_async_engine(
        admin_url, poolclass=NullPool, isolation_level="AUTOCOMMIT"
    )
    async with engine.connect() as conn:
        await conn.execute(
            sa.text(f"CREATE DATABASE {test_db_name} TEMPLATE {template_db_name}")
        )
    await engine.dispose()

    return _build_url(url, test_db_name).render_as_string(hide_password=False)


async def drop_database(base_db_url: str, db_name: str) -> None:
    """Drop a test database by name."""
    base_url = sa.make_url(base_db_url)
    admin_url = _admin_url(base_url)

    engine = create_async_engine(
        admin_url, poolclass=NullPool, isolation_level="AUTOCOMMIT"
    )
    async with engine.connect() as conn:
        await conn.execute(sa.text(f"DROP DATABASE IF EXISTS {db_name}"))
    await engine.dispose()

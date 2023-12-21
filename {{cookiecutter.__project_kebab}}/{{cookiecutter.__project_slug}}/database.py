"""
This module controls settings for tortoise orm
and provides a decorator for connecting to database
"""


from contextlib import asynccontextmanager
from typing import Any

import tortoise
import tortoise.connection

__all__ = ["get_tortoise_orm_settings", "connect_database"]


def get_tortoise_orm_settings(db_url: str) -> dict[str, Any]:
    """
    Application-wide database connection settings
    used in generating/applying migrations, running server and in tests
    """
    return {
        "connections": {"default": db_url},
        "apps": {
            "models": {
                "models": ["{{cookiecutter.__project_slug}}.models", "aerich.models"],
                "default_connection": "default",
            },
        },
    }


async def _init_orm(db_url: str) -> None:
    await tortoise.Tortoise.init(config=get_tortoise_orm_settings(db_url))


async def _close_orm() -> None:
    await tortoise.connection.connections.close_all()


@asynccontextmanager
async def connect_database(db_url: str):
    """
    Main decorator for connecting/disconnecting from database
    used in tests and in running server
    """
    await _init_orm(db_url)
    try:
        yield
    finally:
        await _close_orm()

"""
This module provides a ConnectionPool class for managing database connections
using SQLAlchemy's asynchronous engine and session maker.
"""

from types import TracebackType
from typing import Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from {{cookiecutter.__project_slug}}.storage.db_utils import normalize_db_url


class ConnectionPool:
    def __init__(self, db_url: str, echo: bool = False):
        self._engine = create_async_engine(normalize_db_url(db_url), echo=echo)
        self._async_session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False
        )
        self._inside_context = False

    @property
    def engine(self):
        assert self._inside_context
        return self._engine

    def new_session(self) -> AsyncSession:
        assert self._inside_context
        return self._async_session_factory()

    async def close(self):
        await self._engine.dispose()

    async def __aenter__(self):
        self._inside_context = True
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ):
        await self.close()
        self._inside_context = False

"""
This module provides a ConnectionPool class for managing database connections
using SQLAlchemy's asynchronous engine and session maker.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class ConnectionPool:
    def __init__(self, db_url: str, echo: bool = False):
        self.engine = create_async_engine(db_url, echo=echo)
        self.async_session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    def session(self):
        return AsyncSession(self.engine, expire_on_commit=False)

    def new_session(self) -> AsyncSession:
        return self.async_session_factory()

    async def close(self):
        # for AsyncEngine created in function scope, close and
        # clean-up pooled connections
        await self.engine.dispose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

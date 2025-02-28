"""
common fixtures and classes for tests
"""
import io
import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, Generator, List

import httpx
import pytest
import pytest_asyncio

from {{cookiecutter.__project_slug}}.application_context import ApplicationContext, AppSettings
from {{cookiecutter.__project_slug}}.main import make_app
from {{cookiecutter.__project_slug}}.storage.connection_pool import ConnectionPool
from {{cookiecutter.__project_slug}}.storage.models import Base

from .slog import GcpStructuredFormatter


class JsonLogs(io.StringIO):
    def parse(self) -> List[Dict[str, Any]]:
        lines = list()
        for line in self.getvalue().splitlines():
            if not line:
                continue
            lines.append(json.loads(line))
        return lines


@pytest.fixture()
def structured_logs_capture() -> Generator[JsonLogs, None, None]:
    output = JsonLogs()

    root_logger = logging.getLogger()

    # Copy existing loggers and clear the array
    # (do not just re-assign so references to old handlers list remain valid)
    handlers = root_logger.handlers.copy()
    root_logger.handlers.clear()

    # Add stream logger that writes to our output
    handler = logging.StreamHandler(output)

    handler.formatter = GcpStructuredFormatter()

    root_logger.handlers.append(handler)

    try:
        yield output
    finally:
        # Return loggers back
        root_logger.handlers.clear()
        root_logger.handlers.extend(handlers)


TEST_SETTINGS = AppSettings(
    db_url=os.environ.get("TEST_DB_URL", "sqlite+aiosqlite:///:memory:"),
    host="127.0.0.1",
    port=8000,
    root_path="",
    debug=False,
)


@pytest_asyncio.fixture(scope="module")
async def db_connection_pool() -> AsyncGenerator[ConnectionPool, None]:
    """Connection pool fixture for testing repository alone"""
    async with ConnectionPool(TEST_SETTINGS.db_url) as connection_pool:
        async with connection_pool.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield connection_pool
        async with connection_pool.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="module")
async def api_client(
    db_connection_pool: ConnectionPool,  # pylint: disable=redefined-outer-name
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Client fixture for testing the application APIs"""
    application_context = ApplicationContext.create_with_settings(
        db_connection_pool, TEST_SETTINGS
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=make_app(application_context)),
        base_url="http://test",
    ) as aclient:
        yield aclient

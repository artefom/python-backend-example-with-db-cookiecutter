# pylint: disable=missing-module-docstring
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from {{cookiecutter.__project_slug}}.storage.connection_pool import ConnectionPool


@pytest.mark.asyncio
async def test_connection_pool():
    db_url = "sqlite+aiosqlite:///:memory:"
    with patch.object(ConnectionPool, "close", return_value=None) as mock_close:
        async with ConnectionPool(db_url) as pool:
            async with pool.new_session() as session:
                assert isinstance(session, AsyncSession)
            await pool.engine.dispose()  # do it manually since we mocked close
        mock_close.assert_called_once()

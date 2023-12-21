"""
Example unit tests file
"""

import pytest

from tests.conftest import AppClient


@pytest.mark.asyncio
async def test_health(client: AppClient) -> None:
    """
    Example test of health endpoint
    """

    response = await client.health()

    assert response.status_code == 200

"""
Example unit tests file
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(api_client: AsyncClient) -> None:
    response = await api_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_index(api_client: AsyncClient) -> None:
    response = await api_client.get("/docs")
    assert response.status_code == 200

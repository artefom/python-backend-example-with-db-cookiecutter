"""
Global intergration test configuration
with fixtures
"""

from typing import AsyncGenerator

import httpx
import pytest_asyncio
from tortoise import Tortoise

from {{cookiecutter.__project_slug}}.database import connect_database
from {{cookiecutter.__project_slug}}.main import make_app


class AppClient:
    """
    Wrapper around API of application
    that will be used during testing
    """

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def health(self) -> httpx.Response:
        return await self.client.get("/health")


# Global application that is created only once
APP = make_app("")


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AppClient, None]:
    async with connect_database("sqlite://:memory:"):
        await Tortoise.generate_schemas()
        try:
            async with httpx.AsyncClient(app=APP, base_url="http://test") as aclient:
                yield AppClient(aclient)
        finally:
            await Tortoise._drop_databases()  # pylint: disable=[W0212,]

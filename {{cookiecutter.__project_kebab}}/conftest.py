"""
Common test fixtures.

WARNING: This file should be located in the project's root for the
pytest_* hooks to work properly (start only one test DB container even with xdist).
"""

import logging
import os
from typing import Any, AsyncGenerator, Generator

import httpx
import pytest
import pytest_asyncio
import sqlalchemy as sa
from testcontainers.postgres import PostgresContainer

from {{cookiecutter.__project_slug}}.application_context import ApplicationContext, AppSettings
from {{cookiecutter.__project_slug}}.main import make_app
from {{cookiecutter.__project_slug}}.slog import GcpStructuredFormatter
from {{cookiecutter.__project_slug}}.storage.connection_pool import ConnectionPool
from {{cookiecutter.__project_slug}}.storage.db_utils import normalize_db_url
from {{cookiecutter.__project_slug}}.testing_utils.db_setup import (
    create_test_database_from_template,
    drop_database,
    setup_template_database,
)
from {{cookiecutter.__project_slug}}.testing_utils.log import JsonLogs

_PG_COMMAND = [
    "postgres",
    "-c",
    "fsync=off",
    "-c",
    "full_page_writes=off",
    "-c",
    "synchronous_commit=off",
]

# Make sure to keep the version in sync with .gitlab-ci.yml and GCP instance
_PG_IMAGE = "postgres:18"


def _get_db_url_from_container(container: Any) -> str:
    return container.get_connection_url(driver="asyncpg")


def pytest_xdist_setupnodes(config: pytest.Config) -> None:
    """Start a single PG container for all xdist workers."""
    if os.environ.get("TEST_DB_URL"):
        return
    container = PostgresContainer(_PG_IMAGE).with_command(_PG_COMMAND)
    container.start()
    config.pg_container = container  # type: ignore[attr-defined]
    db_url = _get_db_url_from_container(container)
    config.pg_db_url = db_url  # type: ignore[attr-defined]


def pytest_configure_node(node: Any) -> None:
    """Pass the shared DB URL to each xdist worker via workerinput."""
    if hasattr(node.config, "pg_db_url"):
        db_url = node.config.pg_db_url  # type: ignore[attr-defined]
        node.workerinput["TEST_DB_URL"] = db_url


def pytest_sessionstart(session: pytest.Session) -> None:
    """Expose the shared DB URL in xdist workers."""
    config = session.config
    if hasattr(config, "workerinput"):
        db_url = config.workerinput.get("TEST_DB_URL")  # type: ignore[attr-defined]
        if db_url:
            os.environ["TEST_DB_URL"] = db_url


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Stop the shared xdist PG container after all workers finish."""
    container = getattr(session.config, "pg_container", None)
    if container is not None:
        container.stop()


@pytest.fixture()
def structured_logs_capture() -> Generator[JsonLogs, None, None]:
    output = JsonLogs()

    root_logger = logging.getLogger()

    handlers = root_logger.handlers.copy()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(output)
    handler.formatter = GcpStructuredFormatter()
    root_logger.handlers.append(handler)

    try:
        yield output
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(handlers)


@pytest.fixture(scope="session")
def base_test_db_url() -> Generator[str, None, None]:
    """
    Returns the base PostgreSQL URL for tests. Starts a testcontainer when TEST_DB_URL
    is not set externally.

    To make testcontainers work on MacOS with Colima:
    colima start default --arch aarch64 --vm-type vz --vz-rosetta \\
        --mount-type virtiofs --network-address

    export TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE="/var/run/docker.sock"
    export DOCKER_HOST="unix:///Users/user.name/.colima/default/docker.sock"
    """
    if db_url := os.environ.get("TEST_DB_URL"):
        parsed = normalize_db_url(db_url)
        db_name = parsed.database
        assert db_name and "test" in db_name, (
            "Refusing to operate on a database whose name does not contain 'test'"
        )
        yield parsed.render_as_string(hide_password=False)
        return

    with PostgresContainer(_PG_IMAGE).with_command(_PG_COMMAND) as container:
        yield _get_db_url_from_container(container)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def template_db_name(
    base_test_db_url: str,
) -> AsyncGenerator[str, None]:
    name = await setup_template_database(base_test_db_url)
    yield name
    await drop_database(base_test_db_url, name)


@pytest_asyncio.fixture
async def db_connection_pool(
    base_test_db_url: str,
    template_db_name: str,
) -> AsyncGenerator[ConnectionPool, None]:
    test_db_url = await create_test_database_from_template(
        base_test_db_url, template_db_name
    )
    test_db_name = sa.make_url(test_db_url).database
    assert test_db_name is not None
    try:
        async with ConnectionPool(test_db_url) as pool:
            yield pool
    finally:
        await drop_database(base_test_db_url, test_db_name)


@pytest_asyncio.fixture
async def db_session(
    db_connection_pool: ConnectionPool,
):
    async with db_connection_pool.new_session() as session:
        yield session


@pytest_asyncio.fixture
async def api_client(
    db_connection_pool: ConnectionPool,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Client fixture for testing the application APIs"""
    test_db_url = db_connection_pool.engine.url.render_as_string(hide_password=False)
    settings = AppSettings(
        db_url=test_db_url,
        host="127.0.0.1",
        port=8000,
        root_path="",
        debug=False,
    )
    application_context = ApplicationContext.create_with_settings(
        db_connection_pool, settings
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=make_app(application_context)),
        base_url="http://test",
    ) as aclient:
        yield aclient

"""
Command-line interface of the application

Parses arguments and evironment variables
provides a neat interface with typer

It keeps all imports inside the functions
to allow for fast --help calls
"""

import asyncio
import logging
import logging.config
import os
from typing import TYPE_CHECKING, Any, Awaitable, Callable

import decorator
import typer

if TYPE_CHECKING:
    import aerich  # pylint: disable=[W0611,]

# This variable
# Is initialized upon connection to database
AERICH_APP: "aerich.Command"

logger = logging.getLogger(__name__)

app = typer.Typer(name="{{cookiecutter.__project_kebab}}")

DEFAULT_DB_URL = "sqlite://db.sqlite"


# Global settings
# used in different app commands
STATE = {
    "db_url": DEFAULT_DB_URL,
    "sentry_dsn": "",
    "db_migrations_location": "migrations",
}


# Typer entrypoint
if __name__ == "__main__":
    app()


@decorator.decorator
def with_aerich(func: Callable[[Any], Awaitable[None]], *args: Any, **kwargs: Any):
    """
    Decorator that sets up aerich context for a function
    """
    global AERICH_APP  # pylint: disable=[W0603,]

    from aerich import Command  # pylint: disable=[C0415]
    from tortoise import Tortoise  # pylint: disable=[C0415]

    from {{cookiecutter.__project_slug}}.database import (  # pylint: disable=[C0415]
        get_tortoise_orm_settings,
    )

    db_url = STATE["db_url"]

    # Get migrations location based on database connection type
    # To make sure we do not apply migrations generated on sqlite to postgresql database
    db_engine = db_url.split("://", maxsplit=1)[0]

    async def _run_async():
        global AERICH_APP  # pylint: disable=[W0603,]

        # This thing initializes tortoise database for us
        AERICH_APP = Command(
            tortoise_config=get_tortoise_orm_settings(db_url),
            app="models",
            location=os.path.join(STATE["db_migrations_location"], db_engine),
        )
        await AERICH_APP.init()

        try:
            await func(*args, **kwargs)
        finally:
            await Tortoise.close_connections()
            del AERICH_APP

    return asyncio.run(_run_async())


@app.command()
def run(
    host: str = "127.0.0.1",
    port: int = 8000,
    root_path: str = typer.Option("", envvar="API_ROOT_PATH"),
) -> None:
    """
    Run server
    """
    import uvloop  # pylint: disable=[C0415]

    from {{cookiecutter.__project_slug}}.main import run_server  # pylint: disable=[C0415]

    db_url = STATE["db_url"]

    uvloop.install()

    # Create event loop and run our server
    asyncio.run(run_server(db_url, host=host, port=port, root_path=root_path))


@app.command()
@with_aerich
async def db_downgrade(version: int, delete: bool) -> None:
    """
    Downgrade to specified version.
    """
    await AERICH_APP.downgrade(version=version, delete=delete)


@app.command()
@with_aerich
async def db_heads() -> None:
    """
    Show current available heads in migrate location.
    """
    print(await AERICH_APP.heads())


@app.command()
@with_aerich
async def db_history() -> None:
    """
    List all migrate items.
    """
    _print_table(await AERICH_APP.history())  # type: ignore


@app.command()
@with_aerich
async def db_init() -> None:
    """
    Initialize database (Generate schemas)
    """
    await AERICH_APP.init()


@app.command()
@with_aerich
async def db_migrate_initial(safe: bool = True) -> None:
    """
    Generate initial migration
    """
    await AERICH_APP.init_db(safe=safe)


@app.command()
@with_aerich
async def db_migrate(name: str) -> None:
    """
    Generate migrate changes file.
    """
    from aerich import Migrate  # pylint: disable=[C0415]

    Migrate.app = AERICH_APP.app
    await Migrate.init(AERICH_APP.tortoise_config, AERICH_APP.app, AERICH_APP.location)
    await Migrate.migrate(name=name)


@app.command()
@with_aerich
async def db_upgrade() -> None:
    """
    Upgrade to latest version.
    """
    await AERICH_APP.upgrade(run_in_transaction=True)


@app.callback()
def global_vars(
    verbose: bool = False,
    db_url: str = typer.Option(DEFAULT_DB_URL, envvar="DB_URL"),
    sentry_dsn: str = typer.Option("", envvar="SENTRY_DSN"),
    formatter: str = typer.Option("standard", envvar="LOG_FORMATTER"),
) -> None:
    """
    Hook that sets up
    global variables such as db url or verbosity
    """

    import sentry_sdk  # pylint: disable=[C0415]

    loglevel = logging.INFO

    if verbose:
        loglevel = logging.DEBUG

    STATE["db_url"] = db_url

    # Configure logging
    logging.config.dictConfig(_get_logging_config(loglevel, formatter))

    # Configure setnry
    sentry_sdk.init(
        dsn=sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance
        # monitoring. We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )


def _print_table(table: list[list[str]]) -> None:
    if len(table) == 0:
        return

    if not isinstance(table[0], list):
        table = [[row] for row in table]  # type: ignore

    longest_cols = [
        (max(len(str(row[i])) for row in table) + 3) for i in range(len(table[0]))
    ]
    row_format = "".join(
        ["{:>" + str(longest_col) + "}" for longest_col in longest_cols]
    )
    for row in table:
        print(row_format.format(*row))


def _get_logging_config(level: int, formatter: str):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)-8s| %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "json": {
                "()": "{{cookiecutter.__project_slug}}.slog.GcpStructuredFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": formatter,
            },
        },
        "loggers": {
            "uvicorn": {"level": "WARNING"},
        },
        "root": {
            "handlers": ["console"],
            "level": level,
        },
    }

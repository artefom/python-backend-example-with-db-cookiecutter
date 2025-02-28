"""
Command-line interface of the application

Parses arguments and evironment variables
provides a neat interface with typer

It keeps all imports inside the functions
to allow for fast --help calls
"""

# pylint: disable=import-outside-toplevel

import asyncio
import logging
import logging.config

import typer

from {{cookiecutter.__project_slug}}.application_context import AppSettings

logger = logging.getLogger(__name__)


# This app is referenced by [tool.poetry.scripts] in pyproject.toml
#
# When you install the application `poetry install`
# (to install with lint and tests run `poetry install --with lint,test`)
#
# It makes the 'script' available in your environment. After that
# the application can be executed by simply typing in the console
#
# `{{cookiecutter.__project_kebab}} run`
#
# Or to get some help
# `{{cookiecutter.__project_kebab}} --help`
app = typer.Typer(
    name="{{cookiecutter.__project_kebab}}",
    help="{{cookiecutter.description}}",
)


DEFAULT_DB_URL = "sqlite+aiosqlite:///db.sqlite"


@app.command()
def run(
    host: str = "127.0.0.1",
    port: int = 8000,
    root_path: str = typer.Option("", envvar="API_ROOT_PATH"),
    db_url: str = typer.Option(DEFAULT_DB_URL, envvar="DB_URL"),
    debug: bool = typer.Option(False, envvar="DEBUG"),
) -> None:
    """
    Run server
    """
    import uvloop

    from {{cookiecutter.__project_slug}}.main import run_server

    uvloop.install()

    # Create event loop and run our server
    asyncio.run(
        run_server(
            AppSettings(
                db_url=db_url, host=host, port=port, root_path=root_path, debug=debug
            )
        )
    )


@app.callback()
def global_vars(
    verbose: bool = False,
    sentry_dsn: str | None = typer.Option(None, envvar="SENTRY_DSN"),
    sentry_environment: str | None = typer.Option(None, envvar="SENTRY_ENVIRONMENT"),
    formatter: str = typer.Option("standard", envvar="LOG_FORMATTER"),
) -> None:
    """
    Hook that sets up
    global variables such sentry configuration and logging config.

    Will be executed before any other app command
    """
    import sentry_sdk

    loglevel = logging.INFO

    if verbose:
        loglevel = logging.DEBUG

    # Configure logging
    logging.config.dictConfig(_get_logging_config(loglevel, formatter))

    # Configure setnry
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=sentry_environment,
    )


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

"""
Server entry-point with FastAPI app defined
"""

import logging
import logging.config
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from starlette_exporter import handle_metrics
from starlette_exporter.middleware import PrometheusMiddleware

from {{cookiecutter.__project_slug}}.api import api_router
from {{cookiecutter.__project_slug}}.application_context import ApplicationContext, AppSettings
from {{cookiecutter.__project_slug}}.storage.connection_pool import ConnectionPool
from {{cookiecutter.__project_slug}}.tracking import TrackingMiddleware

logger = logging.getLogger(__name__)

# Configuration of prometheus middleware
BUCKETS = [0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
SKIP_PATHS = ["/health", "/metrics", "/", "/docs", "/openapi.json"]


def make_app(application_context: ApplicationContext) -> FastAPI:
    """
    Creates fastapi APP and registers basic health and metrics endpoints
    """
    root_path = application_context.app_settings.root_path
    app = FastAPI(root_path=root_path)

    app.add_middleware(
        PrometheusMiddleware,
        filter_unhandled_paths=True,
        group_paths=True,
        app_name="{{cookiecutter.__project_kebab}}",
        buckets=BUCKETS,
        skip_paths=[f"{root_path}{path}" for path in SKIP_PATHS],
    )

    # Enable context based tracking
    app.add_middleware(TrackingMiddleware)

    app.add_route("/metrics", handle_metrics)

    # Health check endpoint
    @app.get("/health", include_in_schema=False)
    async def health() -> str:
        """Checks health of application, including database and all systems"""
        return "OK"

    @app.get("/", include_in_schema=False)
    async def index(request: Request) -> RedirectResponse:
        # the redirect must be absolute (start with /) because
        # it needs to handle both trailing slash and no trailing slash
        # /app -> /app/docs
        # /app/ -> /app/docs
        return RedirectResponse(f"{str(request.base_url).rstrip('/')}/docs")

    app.include_router(api_router(application_context))

    # We need to specify custom OpenAPI to add app.root_path to servers
    def custom_openapi() -> Any:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="{{cookiecutter.project_name}}",
            version="0.1.0",
            description="{{cookiecutter.description}}",
            routes=app.routes,
        )
        openapi_schema["servers"] = [{"url": app.root_path}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # noqa

    return app


# This is called in cli.py on "run" command
async def run_server(settings: AppSettings):
    async with ConnectionPool(settings.db_url, settings.debug) as pool:
        application_context = ApplicationContext.create_with_settings(pool, settings)
        app = make_app(application_context)
        config = uvicorn.Config(
            app, settings.host, settings.port, log_config=None, access_log=False
        )
        api_server = uvicorn.Server(config)
        logging.info("Serving on http://%s:%s", settings.host, settings.port)

        await api_server.serve()

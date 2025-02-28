"""
This module is used to store the global services that are used in the application
"""
from dataclasses import dataclass

from {{cookiecutter.__project_slug}}.storage.connection_pool import ConnectionPool
from {{cookiecutter.__project_slug}}.storage.post_repo import PostRepo


@dataclass
class AppSettings:
    db_url: str
    host: str
    port: int
    root_path: str
    debug: bool = False


@dataclass
class ApplicationContext:
    connection_pool: ConnectionPool
    post_repo: PostRepo
    app_settings: AppSettings

    @classmethod
    def create_with_settings(cls, pool: ConnectionPool, settings: AppSettings):
        return cls(
            connection_pool=pool, post_repo=PostRepo(pool), app_settings=settings
        )

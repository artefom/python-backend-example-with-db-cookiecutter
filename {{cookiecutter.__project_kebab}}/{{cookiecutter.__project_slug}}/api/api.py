"""
API implementation
"""
import logging

from fastapi import APIRouter

from {{cookiecutter.__project_slug}}.application_context import ApplicationContext

from . import spec

logger = logging.getLogger(__name__)


class DefaultApi(spec.Api):
    """
    Implementation of the service API
    """

    def __init__(self, application_context: ApplicationContext):
        self.post_repo = application_context.post_repo

    async def echo(self, request: str) -> spec.EchoResponse:
        if request == "error":
            raise spec.EchoExampleError("example error message")
        return spec.EchoResponse(text=f"{request}")

    async def new_post(self, post: spec.PostPayload) -> spec.PostResponse:
        new_post = await self.post_repo.create_post(post.title, post.main_content)
        return spec.PostResponse(
            id=new_post.id, title=new_post.title, main_content=new_post.main_content
        )

    async def view_posts(self) -> spec.PostsListResponse:
        posts = await self.post_repo.view_posts()
        return spec.PostsListResponse(
            data=[
                spec.PostResponse(
                    id=post.id, title=post.title, main_content=post.main_content
                )
                for post in posts
            ]
        )

    async def view_post(self, post_id: int) -> spec.PostResponse:
        post = await self.post_repo.view_post(post_id)
        if post is None:
            raise spec.PostNotFoundError(post_id)
        return spec.PostResponse(
            id=post.id, title=post.title, main_content=post.main_content
        )

    async def update_post(
        self, post_id: int, post: spec.PostPayload
    ) -> spec.PostResponse:
        updated_post = await self.post_repo.update_post(
            post_id, post.title, post.main_content
        )
        if updated_post is None:
            raise spec.PostNotFoundError(post_id)
        return spec.PostResponse(
            id=updated_post.id,
            title=updated_post.title,
            main_content=updated_post.main_content,
        )

    async def delete_post(self, post_id: int) -> None:
        post = await self.post_repo.view_post(post_id)
        if post is None:
            raise spec.PostNotFoundError(post_id)
        await self.post_repo.delete_post(post_id)


def api_router(application_context: ApplicationContext) -> APIRouter:
    return spec.make_router(DefaultApi(application_context))

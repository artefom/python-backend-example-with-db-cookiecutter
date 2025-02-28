# pylint: disable=missing-module-docstring
import pytest

from {{cookiecutter.__project_slug}}.storage.connection_pool import ConnectionPool
from {{cookiecutter.__project_slug}}.storage.post_repo import PostRepo


@pytest.mark.asyncio
async def test_create_record(db_connection_pool: ConnectionPool):
    post_repo = PostRepo(db_connection_pool)
    new_post = await post_repo.create_post(
        title="First Post", main_content="This is the first post"
    )
    assert new_post.id is not None


@pytest.mark.asyncio
async def test_view_record(db_connection_pool: ConnectionPool):
    post_repo = PostRepo(db_connection_pool)
    new_post = await post_repo.create_post(
        title="First Post", main_content="This is the first post"
    )
    post = await post_repo.view_post(new_post.id)
    assert post is not None
    assert post.title == "First Post"


@pytest.mark.asyncio
async def test_update_record(db_connection_pool: ConnectionPool):
    post_repo = PostRepo(db_connection_pool)
    new_post = await post_repo.create_post(
        title="First Post", main_content="This is the first post"
    )
    updated_post = await post_repo.update_post(
        new_post.id, title="Updated Post", main_content="This is the first post"
    )
    assert updated_post is not None
    assert updated_post.title == "Updated Post"


@pytest.mark.asyncio
async def test_delete_record(db_connection_pool: ConnectionPool):
    post_repo = PostRepo(db_connection_pool)
    new_post = await post_repo.create_post(
        title="First Post", main_content="This is the first post"
    )
    await post_repo.delete_post(new_post.id)
    post = await post_repo.view_post(new_post.id)
    assert post is None


@pytest.mark.asyncio
async def test_create_comment(db_connection_pool: ConnectionPool):
    post_repo = PostRepo(db_connection_pool)
    new_post = await post_repo.create_post(
        title="First Post", main_content="This is the first post"
    )
    new_comment = await post_repo.create_comment(
        post_id=new_post.id, content="This is a comment"
    )
    assert new_comment.id is not None


@pytest.mark.asyncio
async def test_view_comment(db_connection_pool: ConnectionPool):
    post_repo = PostRepo(db_connection_pool)
    new_post = await post_repo.create_post(
        title="First Post", main_content="This is the first post"
    )
    new_comment = await post_repo.create_comment(
        post_id=new_post.id, content="This is a comment"
    )
    comment = await post_repo.view_comment(new_comment.id)
    assert comment is not None
    assert comment.content == "This is a comment"


@pytest.mark.asyncio
async def test_update_comment(db_connection_pool: ConnectionPool):
    post_repo = PostRepo(db_connection_pool)
    new_post = await post_repo.create_post(
        title="First Post", main_content="This is the first post"
    )
    new_comment = await post_repo.create_comment(
        post_id=new_post.id, content="This is a comment"
    )
    updated_comment = await post_repo.update_comment(
        new_comment.id, content="Updated Comment"
    )
    assert updated_comment is not None
    assert updated_comment.content == "Updated Comment"


@pytest.mark.asyncio
async def test_delete_comment(db_connection_pool: ConnectionPool):
    post_repo = PostRepo(db_connection_pool)
    new_post = await post_repo.create_post(
        title="First Post", main_content="This is the first post"
    )
    new_comment = await post_repo.create_comment(
        post_id=new_post.id, content="This is a comment"
    )
    await post_repo.delete_comment(new_comment.id)
    comment = await post_repo.view_comment(new_comment.id)
    assert comment is None

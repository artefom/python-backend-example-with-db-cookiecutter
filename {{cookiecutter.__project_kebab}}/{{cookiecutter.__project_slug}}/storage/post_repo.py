"""
This is example module for the PostRepo class.
"""
from sqlalchemy.future import select

from {{cookiecutter.__project_slug}}.storage.connection_pool import ConnectionPool

from .models import Comment, Post


class PostRepo:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    async def create_post(self, title: str, main_content: str) -> Post:
        async with self.pool.new_session() as session, session.begin():
            new_post = Post(title=title, main_content=main_content)
            session.add(new_post)
            return new_post

    async def view_post(self, post_id: int) -> Post | None:
        async with self.pool.new_session() as session, session.begin():
            result = await session.execute(select(Post).filter_by(id=post_id))
            return result.scalars().first()

    async def view_posts(self) -> list[Post]:
        async with self.pool.new_session() as session, session.begin():
            result = await session.execute(select(Post))
            return list(result.scalars().all())

    async def update_post(
        self, post_id: int, title: str, main_content: str
    ) -> Post | None:
        async with self.pool.new_session() as session, session.begin():
            result = await session.execute(select(Post).filter_by(id=post_id))
            post = result.scalars().first()
            if post:
                post.title = title
                post.main_content = main_content
            return post

    async def delete_post(self, post_id: int) -> None:
        async with self.pool.new_session() as session, session.begin():
            result = await session.execute(select(Post).filter_by(id=post_id))
            post = result.scalars().first()
            if post:
                await session.delete(post)

    async def create_comment(self, post_id: int, content: str) -> Comment:
        async with self.pool.new_session() as session, session.begin():
            new_comment = Comment(post_id=post_id, content=content)
            session.add(new_comment)
            return new_comment

    async def view_comment(self, comment_id: int) -> Comment | None:
        async with self.pool.new_session() as session, session.begin():
            result = await session.execute(select(Comment).filter_by(id=comment_id))
            return result.scalars().first()

    async def update_comment(self, comment_id: int, content: str) -> Comment | None:
        async with self.pool.new_session() as session, session.begin():
            result = await session.execute(select(Comment).filter_by(id=comment_id))
            comment = result.scalars().first()
            if comment:
                comment.content = content
            return comment

    async def delete_comment(self, comment_id: int) -> None:
        async with self.pool.new_session() as session, session.begin():
            result = await session.execute(select(Comment).filter_by(id=comment_id))
            comment = result.scalars().first()
            if comment:
                await session.delete(comment)

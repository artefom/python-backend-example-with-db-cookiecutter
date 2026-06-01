"""
Example Post and Comment models.
"""
from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from {{cookiecutter.__project_slug}}.storage.models import Base
from {{cookiecutter.__project_slug}}.storage.models.custom_types import DatetimeWithTimezone


class Post(Base):
    __tablename__ = "posts"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    main_content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DatetimeWithTimezone,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DatetimeWithTimezone,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    comments: Mapped[List["Comment"]] = relationship()


class Comment(Base):
    __tablename__ = "comments"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DatetimeWithTimezone,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DatetimeWithTimezone,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

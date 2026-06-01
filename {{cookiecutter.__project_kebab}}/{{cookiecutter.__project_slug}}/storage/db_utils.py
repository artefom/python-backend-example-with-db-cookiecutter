"""
DB utils
"""

from typing import Union

import sqlalchemy as sa


def normalize_db_url(url: Union[str, sa.URL]) -> sa.URL:
    """Normalize any postgres:// or postgresql:// URL to postgresql+asyncpg."""
    parsed = sa.make_url(url)
    if parsed.drivername in ("postgres", "postgresql"):
        parsed = parsed.set(drivername="postgresql+asyncpg")
    return parsed

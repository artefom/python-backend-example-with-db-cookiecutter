"""
Custom SQLAlchemy types.
"""

from datetime import date, datetime, timezone

import sqlalchemy as sa
from sqlalchemy import Dialect


# pylint: disable=abstract-method, too-many-ancestors
class DatetimeWithTimezone(sa.TypeDecorator):
    """
    Ensures datetime objects are always stored in UTC and returned with UTC timezone.
    Raises TypeError if a naive datetime (without tzinfo) is stored.
    """

    impl = sa.DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(
        self, value: datetime | date | None, dialect: Dialect
    ) -> datetime | None:
        if value is not None:
            # isinstance(datetime.now(), date) is True, so we have to check the type.
            # pylint: disable=unidiomatic-typecheck
            if type(value) == date:
                value = datetime(
                    value.year, value.month, value.day, tzinfo=timezone.utc
                )

            assert isinstance(value, datetime), type(value)

            if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
                raise TypeError("tzinfo is required")

            return value.astimezone(timezone.utc)

        return value

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is not None:
            assert value.tzinfo is not None, value
        return value

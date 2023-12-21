"""
Definition of database schemas,
this file is referenced at database.py to make tortoise aware of it
"""

from tortoise.fields import CharField, DatetimeField, IntField
from tortoise.models import Model


class TestModel(Model):
    """
    Example of database model
    """

    id = IntField(pk=True, unique=True, index=True)
    created_at = DatetimeField(auto_now_add=True, index=True)
    test_field = CharField(null=True, max_length=200)

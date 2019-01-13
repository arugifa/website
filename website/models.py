from collections.abc import Iterable
from typing import List

import sqlalchemy

from website import db
from website.exceptions import MultipleResultsFound


class BaseModel(db.Model):
    """Base class to be inherited by all other models."""

    __abstract__ = True

    @classmethod
    def all(cls) -> List:
        """Return all items."""
        return cls.query.all()

    @classmethod
    def filter(cls, **kwargs) -> List:
        """Filter items.

        Search parameters can be given as keyword arguments.
        """
        query = cls.query

        for key, value in kwargs:
            column = getattr(cls, key)

            if isinstance(value, Iterable):
                query = query.filter(column.in_(value))
            else:
                query = query.filter(column == value)

        return query.all()

    # TODO: How to use typing annotations here? (01/2019)
    # Doing like that: `def find(cls, **kwargs) -> BaseModel:`
    # raises a "F821 undefined name" error.
    @classmethod
    def find(cls, **kwargs):
        """Look for a specific item.

        Search parameters should be given as keyword arguments.

        :raise website.exceptions.MultipleResultsFound:
            if several articles are found.
        """
        try:
            return cls.query.filter_by(**kwargs).one_or_none()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            raise MultipleResultsFound

    def save(self):
        """Save the item into database."""
        db.session.add(self)

"""Base classes to be inherited from by models all over the website."""

from collections.abc import Iterable
from typing import List, Optional

import sqlalchemy

from website import db
from website.exceptions import MultipleResultsFound


class BaseModel(db.Model):
    """Base class to be inherited by all other models."""

    __abstract__ = True

    # Class Methods

    @classmethod
    def all(cls) -> List['BaseModel']:
        """Return all items."""
        return cls.query.all()

    @classmethod
    def filter(cls, **kwargs: str) -> List['BaseModel']:
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

    @classmethod
    def find(cls, **kwargs: str) -> Optional['BaseModel']:
        """Look for a specific item.

        Search parameters should be given as keyword arguments.

        :raise website.exceptions.MultipleResultsFound:
            if several articles are found.
        """
        try:
            return cls.query.filter_by(**kwargs).one_or_none()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            raise MultipleResultsFound

    # Instance Methods

    def delete(self) -> None:
        """Remove item from database."""
        db.session.delete(self)

    def save(self) -> None:
        """Save item into database."""
        db.session.add(self)


class Document(BaseModel):
    """Base class for all documents (.e.g., blog articles, notes, etc.)."""

    __abstract__ = True

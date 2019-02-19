"""Base classes to be inherited from by models all over the website."""

from collections.abc import Iterable
from datetime import date
from typing import List, Optional

import sqlalchemy.exc as sql_errors
import sqlalchemy.orm.exc as orm_errors

from website import db
from website.exceptions import (
    ItemAlreadyExisting, ItemNotFound, MultipleItemsFound)


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

        for key, value in kwargs.items():
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
            return cls.query.filter_by(**kwargs).one()
        except orm_errors.NoResultFound:
            raise ItemNotFound
        except orm_errors.MultipleResultsFound:
            raise MultipleItemsFound

    # Instance Methods

    def delete(self) -> None:
        """Remove item from database."""
        db.session.delete(self)
        db.session.flush([self])

    def save(self) -> None:
        """Save item into database."""
        db.session.add(self)

        try:
            db.session.flush([self])
        except sql_errors.IntegrityError:
            raise ItemAlreadyExisting(self)


class Document(BaseModel):
    """Base class for all documents (.e.g., blog articles, notes, etc.)."""

    __abstract__ = True

    uri = db.Column(db.String, unique=True, nullable=False)
    publication_date = db.Column(db.Date, default=date.today, nullable=False)
    last_update = db.Column(db.Date)

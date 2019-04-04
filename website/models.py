"""Base classes to be inherited from by models all over the website."""

import re
from collections.abc import Iterable
from datetime import date
from typing import List, Optional, Union

import sqlalchemy.exc as sql_errors
import sqlalchemy.orm.exc as orm_errors
from sqlalchemy.ext.declarative import declared_attr

from website import db
from website import exceptions


class BaseModel(db.Model):
    """Base class to be inherited by all other models."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    uri = db.Column(db.String, unique=True, nullable=False)

    # Model Properties

    @declared_attr
    def __tablename__(cls):  # noqa: N805
        model_name = cls.__name__

        if model_name.endswith('y'):
            plural_name = "{}ies".format(model_name[:-1])
        else:
            plural_name = "{}s".format(model_name)

        return re.sub('(?!^)([A-Z]+)', r'_\1', plural_name).lower()

    @property
    def doc_type(self) -> str:
        """Return the model's name in lowercase."""
        model_name = self.__class__.__name__
        return re.sub(r'(?!^)([A-Z]+)', r' \1', model_name).lower()

    # Class Methods

    @classmethod
    def all(cls) -> List['BaseModel']:
        """Return all items."""
        return cls.query.all()

    @classmethod
    def filter(cls, **kwargs: Union[str, Iterable]) -> List['BaseModel']:
        """Filter items.

        Search parameters can be given as keyword arguments.
        """
        # return Filter(cls, **kwargs)
        query = cls.query

        for key, value in kwargs.items():
            column = getattr(cls, key)

            if isinstance(value, str):
                query = query.filter(column == value)
            else:
                query = query.filter(column.in_(value))

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
            raise exceptions.ItemNotFound
        except orm_errors.MultipleResultsFound:
            raise exceptions.MultipleItemsFound

    # Instance Methods

    def exists(self):
        """Check if an item with the same :attr:`uri` already exists."""
        column = self.__class__.uri
        value = getattr(self, column.name)
        item = self.__class__.query.filter(column == value)
        return db.session.query(item.exists()).scalar()

    def delete(self) -> None:
        """Remove item from database."""
        db.session.delete(self)
        db.session.flush([self])

    def save(self) -> None:
        """Save item into database."""
        db.session.add(self)

        try:
            db.session.flush([self])
        except sql_errors.IntegrityError as exc:
            raise exceptions.InvalidItem(self, exc)


class Document(BaseModel):
    """Base class for all documents (.e.g., blog articles, notes, etc.)."""

    __abstract__ = True

    publication_date = db.Column(db.Date, default=date.today, nullable=False)
    last_update = db.Column(db.Date, onupdate=date.today)

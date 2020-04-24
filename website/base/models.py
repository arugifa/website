"""Base classes to be inherited by models all over the website."""

import re
from operator import attrgetter
from typing import Any, ClassVar, Iterable, List, Optional, Union

import sqlalchemy.exc as sql_errors
import sqlalchemy.orm.exc as orm_errors
from sortedcontainers import SortedKeyList
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.properties import RelationshipProperty

from website import db
from website import exceptions


# Base Models

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
        except (sql_errors.IntegrityError, sql_errors.InterfaceError) as exc:
            raise exceptions.InvalidItem(self, exc)

    def update(self, **attributes: Any) -> None:
        """Update in-place the item in database with new attributes.

        :raise AttributeError: when trying to set attributes which don't exist.
        """
        for field, value in attributes.items():
            setattr(self, field, value)

        self.save()


class BaseDocument(BaseModel):
    """Base class for all documents (.e.g., blog articles, notes, etc.)."""

    __abstract__ = True

    category = ClassVar[RelationshipProperty]
    _tags = ClassVar[RelationshipProperty]

    @declared_attr
    def category_id(self):
        """Must use `declared_attr` when setting foreign keys on base classes."""
        return db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    @hybrid_property
    def tags(self) -> 'TagList':
        """Return sorted tags."""
        return self._tags

    @tags.setter
    def tags(self, value: Iterable):
        """Sort tags when overwriting them."""
        self._tags = TagList(value)


# Custom Types

class TagList(SortedKeyList):
    """Keep tags always sorted.

    This makes testing easier, especially when documents are updated
    and that tags are inserted asynchronously.
    """

    def __init__(self, tags: Iterable['Tag'] = None):
        SortedKeyList.__init__(self, tags, key=attrgetter('uri'))

    def append(self, tag: 'Tag'):  # noqa: D401
        """Method required by SQLAlchemy.

        In order to populate the list when loading tags from database.
        """
        return self.add(tag)

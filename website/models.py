from collections.abc import Iterable
from datetime import date

import sqlalchemy

from website import db
from website.exceptions import MultipleResultsFound


class BaseModel(db.Model):
    __abstract__ = True

    @classmethod
    def all(cls):
        return cls.query.all()

    @classmethod
    def filter(cls, **kwargs):
        query = cls.query

        for key, value in kwargs:
            column = getattr(cls, key)

            if isinstance(value, Iterable):
                query = query.filter(column.in_(value))
            else:
                query = query.filter(column == value)

        return query.all()

    @classmethod
    def find(cls, **kwargs):
        """Search for a unique article.

        Search parameters should be given as keyword arguments.

        :rtype: a :class:`.Article` instance if found; ``None`` otherwise.
        :raise: :class:`.MultipleResultsFound` if several articles are found.
        """
        try:
            return cls.query.filter_by(**kwargs).one_or_none()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            raise MultipleResultsFound

    def save(self):
        db.session.add(self)


class BaseArticle(BaseModel):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    publication_date = db.Column(db.Date, default=date.today, nullable=False)
    last_update = db.Column(db.Date)
    uri = db.Column(db.String, unique=True, nullable=False)


class Tag(BaseModel):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False)
    uri = db.Column(db.String, unique=True, nullable=False)

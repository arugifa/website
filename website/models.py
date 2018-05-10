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


class Document(BaseModel):
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

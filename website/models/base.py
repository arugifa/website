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

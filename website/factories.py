from datetime import date

from factory import LazyFunction, Sequence
from factory.alchemy import SQLAlchemyModelFactory

from . import db
from . import models


class BaseSQLAlchemyFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = db.session

        # Database session is committed after fixtures creation.
        # So we don't have to do it manually in a Flask shell for example...
        sqlalchemy_session_persistence = 'commit'


class DocumentFactory(BaseSQLAlchemyFactory):
    class Meta:
        abstract = True

    publication_date = LazyFunction(date.today)
    last_update = None


class TagFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.Tag

    name = Sequence(lambda n: f"Tag {n}")
    uri = Sequence(lambda n: f'tag_{n}')

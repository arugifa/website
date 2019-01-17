"""Base classes to be inherited from by factories all over the website."""

from factory.alchemy import SQLAlchemyModelFactory

from website import db


class BaseDatabaseFactory(SQLAlchemyModelFactory):
    """Base factory for every model."""

    class Meta:
        abstract = True
        sqlalchemy_session = db.session

        # Database session is committed after fixtures creation.
        # So we don't have to do it manually, when playing around
        # in a Flask shell for example...
        sqlalchemy_session_persistence = 'commit'

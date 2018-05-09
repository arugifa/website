from factory.alchemy import SQLAlchemyModelFactory

from website import db


class BaseSQLAlchemyFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = db.session

        # Database session is committed after fixtures creation.
        # So we don't have to do it manually in a Flask shell for example...
        sqlalchemy_session_persistence = 'commit'

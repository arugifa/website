import os
from pathlib import Path


class DefaultConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # TODO: Do not set manually a default value.
    # For now, Flask-SQLAlchemy prints a warning when this setting is not set.
    # This is especially annoying when running the tests.
    # However, a default value should be set to False in a near future.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class DevelopmentConfig(DefaultConfig):
    DEBUG = True
    FREEZER_DESTINATION = Path(__file__).parents[1] / 'build'
    FREEZER_IGNORE_404_NOT_FOUND = True  # For RackSpace 404 error page
    FREEZER_REDIRECT_POLICY = 'error'

    # The database file's path can be given as an environment variable.
    # If the path is relative, it will first be made absolute in order to
    # avoid to create the database next to the source code (default behavior
    # of Flask-SQLAlchemy).
    #
    # Also, by default and for troubleshooting purpose, we do not store
    # the database in memory. It is hence possible to launch a demo server
    # and debug the application by launching a shell in parallel.
    DATABASE_DEFAULT_PATH = Path('/tmp/website.sqlite')
    DATABASE_USER_PATH_ENV = 'WEBSITE_DB'
    DATABASE_USER_PATH = None
    SQLALCHEMY_DATABASE_URI = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.DATABASE_USER_PATH is None:
            db_path = os.environ.get(self.DATABASE_USER_PATH_ENV)

            if db_path is not None:
                self.DATABASE_USER_PATH = Path(db_path).resolve()
        else:
            # Ensure database's path is absolute, to avoid Flask-SQLAlchemy
            # to create the database next to the source code.
            self.DATABASE_USER_PATH = self.DATABASE_USER_PATH.resolve()

        self.SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(
            self.DATABASE_USER_PATH or self.DATABASE_DEFAULT_PATH)


class TestingConfig(DefaultConfig):
    TESTING = True

"""Different configurations, to be used in different environments."""

import os
from pathlib import Path

IN_MEMORY_DATABASE = 'sqlite:///:memory:'


class DefaultConfig:
    """Default configuration."""

    #: Store database in memory by default, for faster access.
    SQLALCHEMY_DATABASE_URI = IN_MEMORY_DATABASE

    # TODO: Do not set manually a default value (12/2018)
    # For now, Flask-SQLAlchemy prints a warning when this setting is not set.
    # This is especially annoying when running the tests.
    # However, a default value should be set to False in a near future.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class DevelopmentConfig(DefaultConfig):
    """Development configuration.

    :param SQLALCHEMY_DATABASE_URI: connection string for SQLAlchemy.
    """

    #: Forward errors to web clients, and auto-reload source code.
    DEBUG = True

    #: Where to store the static version of the website.
    FREEZER_DESTINATION = Path(__file__).parents[1] / 'frozen'
    #: Ignore HTTP 404 errors when freezing the website,
    #: as it is mandatory to have a 404 page when uploading to RackSpace.
    FREEZER_IGNORE_404_NOT_FOUND = True
    # TODO: explain why we raise (12/2018)
    #: Raise an error when finding an HTTP redirection.
    FREEZER_REDIRECT_POLICY = 'error'

    #: SQLite database file's path.
    DATABASE_PATH = None
    #: Database's path can also be set via an environment variable.
    #: Value given at runtime takes precedence over it.
    ENV_DATABASE_PATH = 'WEBSITE_DB'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.DATABASE_PATH = \
            self.DATABASE_PATH or os.environ.get(self.ENV_DATABASE_PATH)

        # Ensure database's path is absolute, to avoid Flask-SQLAlchemy
        # to create the database next to the source code by accident.
        try:
            self.DATABASE_PATH = Path(self.DATABASE_PATH).resolve(strict=True)
        except TypeError:
            # If no database's path is defined, use the default one.
            pass
        except FileNotFoundError:
            error = f"No database found at {self.DATABASE_PATH}"
            raise FileNotFoundError(error)
        else:
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{self.DATABASE_PATH}'


class TestingConfig(DefaultConfig):
    """Testing configuration."""

    #: Let's raise exceptions during tests, to know what's happening when an
    #: internal server error happens.
    TESTING = True

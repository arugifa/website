import os
from pathlib import Path

IN_MEMORY_DATABASE = 'sqlite:///:memory:'


class DefaultConfig:
    #: Database URI.
    SQLALCHEMY_DATABASE_URI = IN_MEMORY_DATABASE

    # TODO: Do not set manually a default value.
    # For now, Flask-SQLAlchemy prints a warning when this setting is not set.
    # This is especially annoying when running the tests.
    # However, a default value should be set to False in a near future.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class DevelopmentConfig(DefaultConfig):
    #: Forward errors to web clients, and auto-reload source code.
    DEBUG = True
    #: Where to store the static version of the website.
    FREEZER_DESTINATION = Path(__file__).parents[1] / 'frozen'
    #: Ignore HTTP 404 errors, as we need a 404 page for RackSpace Cloud Files.
    FREEZER_IGNORE_404_NOT_FOUND = True
    # TODO: explain why we raise...
    #: Raise an error when finding an HTTP redirection.
    FREEZER_REDIRECT_POLICY = 'error'

    #: Database's path can be set via an environment variable.
    DATABASE_PATH_ENV = 'WEBSITE_DB'
    #: Database's path can also be given at runtime,
    #: in which case it overrides any value set via the environment variable.
    DATABASE_PATH = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.DATABASE_PATH = \
            self.DATABASE_PATH or os.environ.get(self.DATABASE_PATH_ENV)

        # Ensure database's path is absolute, to avoid Flask-SQLAlchemy
        # to create the database next to the source code.
        try:
            self.DATABASE_PATH = Path(self.DATABASE_PATH).resolve(strict=True)
        except TypeError:
            # If no database's path is defined, use in-memory database.
            pass
        except FileNotFoundError:
            error = f"No database found at {self.DATABASE_PATH}"
            raise FileNotFoundError(error)
        else:
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{self.DATABASE_PATH}'


class TestingConfig(DefaultConfig):
    #: Let raise exceptions.
    TESTING = True

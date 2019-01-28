"""Main entry point to manage content of my website."""

import logging
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path, PurePath
from typing import Callable, Iterable, List, Mapping

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from website import db
from website.exceptions import DocumentLoadingError
from website.models import Document

logger = logging.getLogger(__name__)


class ContentManager:
    """Manage content life cycle.

    Content of the website is stored inside a Git repository, in order to have
    content versionning. The structure of this repository should look like::

        blog/
            2019/
                01-31. first_article_of_the_year.adoc
                12-31. last_article_of_the_year.adoc

    Documents in this repository are loaded, processed, and finally stored,
    updated or deleted inside the database.

    :param app:
        ...
    :param repository:
        Git repository's path.
    :param reader:
        function to read documents in the repository.
    :param prompt:
        function to interactively ask questions during documents import,
        when certain things cannot be completely done automatically.
    """

    def __init__(
            self, app: Flask, repository: Path, handlers: Mapping[str, 'DocumentHandler'],
            reader: Callable = open, prompt: Callable = input):
        self.app = app
        self.repository = repository
        self.reader = reader
        self.prompt = prompt
        #: Specialized content management helpers (e.g., blog, notes, etc.).
        self.handlers = {
            category: handler(db, reader, prompt)
            for category, handler in self.HANDLERS.items()}

    def update(self, diff: Mapping) -> None:
        with self.app.app_context():
            try:
                self.add(diff['added'])
                self.modify(diff['modified'])
                self.rename(diff['renamed'])
                self.delete(diff['deleted'])

                db.session.commit()

            except Exception:
                db.session.rollback()
                logger.error("No change has been made to the database")

    def add(self, paths: Iterable[Path]) -> List[Document]:
        """Insert documents into database.

        :param paths: document paths.
        """
        documents = []

        for path in paths:
            path = path.relative_to(self.repository)
            handler = self.get_handler(path)
            document = handler.add(path)
            documents.add(document)

        return documents

    def delete(self, paths: Iterable[Path]) -> None:
        """Delete documents from database.

        :param paths: document paths.
        """
        for path in paths:
            path = path.relative_to(self.repository)
            handler = self.get_handler(path)
            handler.delete(path)

    def modify(self, paths: Iterable[Path]) -> List[Document]:
        """Update documents in database.

        :param paths: document paths.
        """
        documents = []

        for path in paths:
            path = path.relative_to(self.repository)
            handler = self.get_handler(path)
            document = handler.update(path)
            documents.add(document)

        return documents

    def rename(self, paths: Iterable[Path]) -> List[Document]:
        """Rename documents in database.

        :param paths: document paths.
        """
        documents = []

        for src, dst in paths:
            try:
                assert src.parent == dst.parent
            except AssertionError:
                print(
                    f"Cannot move {src.name} from {src.parent} to {dst.parent}: "  # noqa: E501
                    "it should stay in the same top-level directory")
                raise

            src = src.relative_to(self.repository)
            dst = dst.relative_to(self.repository)
            handler = self.get_handler(src)
            document = handler.rename(src, dst)
            documents.add(document)

        return documents

    # Helpers

    @staticmethod
    def get_category(path: Path):
        """Return the type of a document, based on its path.

        :param path:
            document's path, relative to its Git repository, e.g.:

            - <CATEGORY>/<URI>.<EXTENSION>
            - <CATEGORY>/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>

        :raise ValueError:
            if the document is stored in the top-level directory,
            in which case, it's not possible to guess its category.
        """
        try:
            return list(path.parents)[-2].name
        except IndexError:
            error = 'Document "%s" must be classified in a directory'
            logger.exception(error, path)
            raise ValueError(error % path)

    def get_handler(self, path: Path) -> 'DocumentHandler':
        """Return handler to process a document.

        :param path:
            document's path, relative to its Git repository
            (e.g., ``<CATEGORY>/<URI>.<EXTENSION>``).
        :raise KeyError:
            when no handler is found.
        :raise ValueError:
            if unable to guess document's category type from its path.
        """
        try:
            category = self.get_category(path)  # ValueError
            return self.handlers[category]  # KeyError
        except (KeyError, ValueError):
            error = "No callback defined for %s"
            logger.error(error, path)
            raise KeyError(error % path)


class BaseDocumentHandler(ABC):
    """Manage documents life cycle.

    Load document sources from local files, and update their state in database.

    :param db:
        website's database.
    :param reader:
        function to read documents in the repository.
    :param prompt:
        function to interactively ask questions during documents import,
        when certain things cannot be completely done automatically.
    """

    def __init__(
            self, db: SQLAlchemy,
            reader: Callable = open, prompt: Callable = input):
        self.db = db
        self.reader = reader
        self.prompt = prompt

    @abstractmethod
    def add(self, path: Path) -> Document:
        """Insert a document into database."""

    @abstractmethod
    def delete(self, path: Path) -> None:
        """Remove a document from database."""

    @abstractmethod
    def rename(self, path: Path) -> Document:
        """Rename a document in database."""

    @abstractmethod
    def update(self, path: Path) -> Document:
        """Update a document in database."""

    # Helpers

    def load(self, path: Path) -> str:
        """Read document's source file.

        :param path: document's path.
        """
        try:
            return self.reader(path).read()
        except (OSError, UnicodeDecodeError) as exc:
            error = "Unable to read %s: %s"
            logger.error(error, path, exc)
            raise DocumentLoadingError(error % (path, exc))

    @staticmethod
    def parse_date(path: PurePath) -> date:
        """Return the creation date of a document, based on its path.

        :param path:
            document's path, relative to its repository
            (e.g., ``blog/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>``).
        :raise ValueError:
            if the  document's path doesn't contain a proper date.
        """
        try:
            year = int(path.parents[0].name)
            month, day = map(int, path.name.split('.')[0].split('-'))
        except (IndexError, TypeError):
            error = 'Path "%s" does not contain a proper date'
            logger.error(error, path)
            raise ValueError(error % path)

        return date(year, month, day)

    @staticmethod
    def parse_uri(path: PurePath) -> str:
        """Return the URI of a document, based on its path.

        :param path:
            document's path, relative to its repository
            (e.g., ``blog/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>``).
        """
        return path.stem.split('.')[-1]


class BaseDocumentReader(ABC):
    def __init__(self):
        #: Path of the currently read document.
        #: Initialized when calling a reader instance later on.
        self.path = None

    def __call__(self, path: Path):
        """Prepare the reader for further reading."""
        self.path = path
        return self

    @abstractmethod
    def read(self) -> str:
        """Effectively read the document located at :attr:`path`.

        :raise OSError: when cannot open the document.
        :raise UnicodeDecodeError: when cannot read the document's content.
        """

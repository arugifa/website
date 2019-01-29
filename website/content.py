"""Main entry point to manage content of my website."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Iterable, List, Mapping

from website.exceptions import DocumentReadingError
from website.models import Document

logger = logging.getLogger(__name__)


@dataclass
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

    :param reader:
        function to read documents in the repository.
    :param prompt:
        function to interactively ask questions during documents import,
        when certain things cannot be completely done automatically.
    """
    handlers: Mapping[str, 'BaseDocumentHandler']
    reader: Callable = open
    prompt: Callable = input

    def update(self, repository: Path, diff: Mapping[str, Iterable[Path]]) -> None:
        """...

        :param repository:
            Git repository's path.
        """
        self.add(repository, diff['added'])
        self.modify(repository, diff['modified'])
        self.rename(repository, diff['renamed'])
        self.delete(repository, diff['deleted'])

    def add(self, repository: Path, paths: Iterable[Path]) -> List[Document]:
        """Insert documents into database.

        :param paths: document paths.
        """
        documents = []

        for path in paths:
            handler = self.get_handler(path)
            document = handler.insert()
            documents.add(document)

        return documents

    def modify(self, paths: Iterable[Path]) -> List[Document]:
        """Update documents in database.

        :param paths: document paths.
        """
        documents = []

        for path in paths:
            handler = self.get_handler(path)
            document = handler.update()
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

            src = src.relative_to(self.repository.path)
            dst = dst.relative_to(self.repository.path)
            handler = self.get_handler(src)
            document = handler.rename(dst)
            documents.add(document)

        return documents

    def delete(self, paths: Iterable[Path]) -> None:
        """Delete documents from database.

        :param paths: document paths.
        """
        for path in paths:
            handler = self.get_handler(path)
            handler.delete()

    # Helpers

    def get_handler(self, repository: Path, document: Path) -> 'BaseDocumentHandler':
        """Return handler to process a document.

        :param file_path:
            document's path, relative to its Git repository
            (e.g., <CATEGORY>/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>).

        :raise KeyError:
            when no handler is found.
        """
        try:
            category = document.parents[0].name
            handler = self.handlers[category]
        except KeyError:
            error = "No callback defined for %s"
            logger.error(error, document)
            raise KeyError(error % document)

        path = repository / document
        return handler(path, self.reader, self.prompt)


@dataclass
class BaseDocumentHandler(ABC):
    """Manage documents life cycle.

    Load document sources from local files, and update their state in database.

    :param path:
        document's path, relative to its repository
        (e.g., ``blog/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>``).
    :param reader:
        function to read documents in the repository.
    :param prompt:
        function to interactively ask questions during documents import,
        when certain things cannot be completely done automatically.
    """
    path: str
    reader: Callable = open
    prompt: Callable = input

    @abstractmethod
    def insert(self) -> Document:
        """Insert a document into database.

        :raise website.exceptions.DocumentAlreadyExists:
            if a conflict happens during document insertion.
        """

    @abstractmethod
    def update(self) -> Document:
        """Update a document in database.

        :raise website.exceptions.DocumentNotFound:
            if the document doesn't exist.
        """

    @abstractmethod
    def rename(self, new_path: Path) -> Document:
        """Rename a document in database.

        :raise website.exceptions.DocumentNotFound:
            if the document doesn't exist.
        """

    @abstractmethod
    def delete(self) -> None:
        """Remove a document from database.

        :raise website.exceptions.DocumentNotFound:
            if the document doesn't exist.
        """

    # Helpers

    def read(self) -> str:
        """Read document's source file.

        :param path: document's path.
        """
        try:
            return self.reader(self.path).read()
        except (OSError, UnicodeDecodeError) as exc:
            error = "Unable to read %s: %s"
            logger.error(error, self.path, exc)
            raise DocumentReadingError(error % (self.path, exc))

    def parse_date(self) -> date:
        """Return the creation date of a document, based on its :attr:`path`."""  # noqa: E501
        try:
            year = int(self.path.parents[0].name)
            month, day = map(int, self.path.name.split('.')[0].split('-'))
        except (IndexError, TypeError):
            error = 'Path "%s" does not contain a proper date'
            logger.error(error, self.path)
            raise ValueError(error % self.path)

        return date(year, month, day)

    def parse_uri(self) -> str:
        """Return the URI of a document, based on its :attr:`path`."""
        return self.path.stem.split('.')[-1]


@dataclass
class BaseDocumentReader(ABC):
    #: Path of the currently read document.
    #: Initialized when calling a reader instance later on.
    path: Path = None

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

"""Main entry point to manage content of my website."""

import logging
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePath
from typing import Callable, ClassVar, Iterable, List, Mapping, Union

import lxml.html
from bs4 import BeautifulSoup

from website.exceptions import (
    ItemAlreadyExisting, ItemNotFound, DocumentLoadingError)
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
    path: Union[Path, PurePath]
    reader: Callable = open
    prompt: Callable = input

    model: ClassVar[Document]
    parser: ClassVar['BaseDocumentSourceParser']

    # Main API

    def insert(self) -> Document:
        """Insert a document into database.

        :raise website.exceptions.ItemAlreadyExisting:
            if a conflict happens during document insertion.
        """
        return self.update(create=True)

    def update(self, uri: str = None, create: bool = False) -> Document:
        """Update a document in database.

        :param uri:
            URI the document currently has in database.
        :param create:
            create the document if it doesn't exist yet in database.
        :raise website.exceptions.ItemNotFound:
            if the document cannot be found, and ``create`` is set to ``False``.
        """  # noqa: E501
        if create:
            uri = self.scan_uri()
            document = self.model(uri=uri)

            if document.exists():
                raise ItemAlreadyExisting(uri)

        elif uri:  # Rename and update
            document = self.model.find(uri=uri)  # Can raise ItemNotFound
            document.uri = self.scan_uri()  # New URI
            document.last_update = date.today()

        else:  # Update only
            uri = self.scan_uri()
            document = self.model.find(uri=uri)  # Can raise ItemNotFound
            document.last_update = date.today()

        self.process(document)
        document.save()

        return document

    def rename(self, new_path: Path) -> Document:
        """Rename (and update) a document in database.

        :raise website.exceptions.ItemNotFound:
            if the document doesn't exist.
        """
        # TODO: Set-up an HTTP redirection (01/2019)
        uri = self.scan_uri()
        handler = self.__class__(new_path, self.reader, self.prompt)
        return handler.update(uri)

    def delete(self) -> None:
        """Remove a document from database.

        :raise website.exceptions.ItemNotFound:
            if the document doesn't exist.
        """
        uri = self.scan_uri()
        document = self.model.find(uri=uri)  # Can raise ItemNotFound
        document.delete()

    # Helpers

    def load(self):
        try:
            with self.reader(self.path) as f:
                source = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            error = "Unable to read %s: %s"
            logger.error(error, self.path, exc)
            raise DocumentLoadingError(error % (self.path, exc))

        return self.parser(source)

    @abstractmethod
    def process(self, document: Document) -> None:
        """Prepare the document in order to save it in database later on."""
        pass

    # Path Scanners

    def scan_uri(self) -> str:
        """Return the URI of a document, based on its :attr:`path`."""
        return self.path.stem.split('.')[-1]


class BaseDocumentSourceParser(AbstractContextManager):
    def __init__(self, source: str):
        self._source = source
        self.source = lxml.html.document_fromstring(source)

    def __exit__(self, *args, **kwargs):
        return super().__exit__(*args, **kwargs)

    def parse_tags(self) -> List[str]:
        """Search the tags of an article, inside its HTML source."""
        html = BeautifulSoup(self._source, 'html.parser')

        try:
            tags = html.head.select_one('meta[name=keywords]')['content']
        except (KeyError, TypeError):
            return list()

        return tags.split(', ')


@dataclass
class BaseDocumentReader(ABC):
    #: Path of the currently read document.
    #: Initialized when calling a reader instance later on.
    path: Path = None

    @contextmanager
    def __call__(self, path: Path):
        """Prepare the reader for further reading."""
        self.path = path
        yield self

    @abstractmethod
    def read(self) -> str:
        """Effectively read the document located at :attr:`path`.

        The returned string must be in HTML format.

        :raise OSError: when cannot open the document.
        :raise UnicodeDecodeError: when cannot read the document's content.
        """

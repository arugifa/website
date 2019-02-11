"""Main entry point to manage content of my website."""

import logging
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePath
from typing import Callable, ClassVar, Iterable, List, Mapping, Union

import lxml.etree
import lxml.html
from lxml.cssselect import CSSSelector

from website import exceptions
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


# Document Processing

@dataclass
class BaseDocumentHandler(ABC):
    """Manage the life cycle of a document in database.

    :param path:
        path of the document's source file, relative to its repository.
        Every document must be written in HTML, and respect a naming
        convention. See documentation of handler subclasses for more info.
    :param reader:
        function to read the documents.
    :param prompt:
        function to interactively ask questions during documents import,
        when certain things cannot be inferred automatically.
    """

    path: Union[Path, PurePath]
    reader: Callable = open
    prompt: Callable = input

    #: Document model clas.
    model: ClassVar[Document]
    #: Document parser class.
    parser: ClassVar['BaseDocumentSourceParser']

    # Main API

    def insert(self) -> Document:
        """Insert document into database.

        :return:
            the newly created document.
        :raise ~.ItemAlreadyExisting:
            if a conflict happens during document insertion.
        """
        return self.update(create=True)  # Can raise ItemAlreadyExisting

    def update(self, uri: str = None, create: bool = False) -> Document:
        """Update document in database.

        :param uri:
            URI the document currently has in database.
        :param create:
            create the document if it doesn't exist yet in database.
        :return:
            the updated document.

        :raise ~.ItemNotFound:
            if the document cannot be found, and ``create`` is set to ``False``.
        """  # noqa: E501
        if create:
            uri = self.scan_uri()
            document = self.model(uri=uri)

            if document.exists():
                raise exceptions.ItemAlreadyExisting(uri)

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

    def rename(self, target: Path) -> Document:
        """Rename (and update) document in database.

        :param target: the new path of document's source file.
        :return: the updated and renamed document.
        :raise ~.ItemNotFound: if the document doesn't exist.
        """
        # TODO: Set-up an HTTP redirection (01/2019)
        uri = self.scan_uri()
        handler = self.__class__(target, self.reader, self.prompt)
        return handler.update(uri)

    def delete(self) -> None:
        """Remove a document from database.

        :raise ~.ItemNotFound: if the document doesn't exist.
        """
        uri = self.scan_uri()
        document = self.model.find(uri=uri)  # Can raise ItemNotFound
        document.delete()

    # Helpers

    def load(self):
        """Read and prepare for parsing the source file located at :attr:`path`.

        :raise ~.DocumentLoadingError:
            when something wrong happens while reading the source file
            (e.g., file not found or unsupported format).
        """  # noqa: E501
        try:
            with self.reader(self.path) as f:
                source = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            raise exceptions.DocumentLoadingError(self, exc)

        return self.parser(source)

    @abstractmethod
    def process(self, document: Document) -> None:
        """Parse :attr:`path` and update a document already loaded from database.

        :param document: the document to update.
        """  # noqa: E501

    # Path Scanners

    def scan_uri(self) -> str:
        """Return document's URI, based on its :attr:`path`."""
        return self.path.stem.split('.')[-1]


class BaseDocumentSourceParser:
    """Parse HTML source of a document.

    :raise ~.DocumentMalformatted: when the given source is not valid HTML.
    """

    def __init__(self, source: str):
        try:
            self.source = lxml.html.document_fromstring(source)
        except lxml.etree.ParserError:
            raise exceptions.DocumentMalformatted(source)

    def parse_title(self) -> str:
        """Look for document's title.

        :raise ~.DocumentTitleMissing: when no title is found.
        """
        parser = CSSSelector('html head title')

        try:
            title = parser(self.source)[0].text_content()
            assert title
        except (AssertionError, IndexError):
            raise exceptions.DocumentTitleMissing(self)

        return title

    def parse_tags(self) -> List[str]:
        """Look for document's tags."""
        parser = CSSSelector('html head meta[name=keywords]')

        try:
            tags = parser(self.source)[0].get('content', '')
            tags = [tag.strip() for tag in tags.split(',')]
            assert all(tags)
        except (AssertionError, IndexError):
            return []

        return tags


# Document Reading

class BaseDocumentReader(ABC):
    """Base class for all document readers.

    Provides a subset of :func:`open`'s API.

    :param pathlib.Path path:
        path of the document to read. Initialized by :meth:`__call__`.
    """

    def __init__(self):
        self.path = None

    def __call__(self, path: Union[str, Path]) -> 'DocumentOpener':
        """Open the document for further reading.

        Can be called directly or used as a context manager.

        :raise OSError: if the document cannot be opened.
        """
        path = Path(path)

        if not path.is_file():
            raise OSError(f"Document doesn't exist: {path}")

        self.path = Path(path)
        return DocumentOpener(self)

    @abstractmethod
    def read(self) -> str:
        """Effectively read the document located at :attr:`path`.

        The returned string must be in HTML format.

        :raise ValueError: when cannot read the document's content.
        """


@dataclass
class DocumentOpener(AbstractContextManager):
    """Helper for :class:`BaseDocumentReader` to open documents.

    :param reader: reader instance opening the document.
    """

    reader: BaseDocumentReader

    def __getattr__(self, name: str):
        """Let :attr:`reader` opening a document as a function call."""
        return getattr(self.reader, name)

    def __enter__(self) -> BaseDocumentReader:
        """Let :attr:`reader` opening a document inside a context manager."""
        return self.reader

    def __exit__(self, *exc) -> None:
        """Nothing done here for the moment..."""
        return

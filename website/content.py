"""Main entry point to manage content of my website."""

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePath
from typing import Callable, ClassVar, Iterable, List, Mapping, Tuple, Union

import lxml.etree
import lxml.html
from lxml.cssselect import CSSSelector

from website import exceptions
from website.models import Document


@dataclass
class ContentManager:
    """Manage website's content life cycle.

    The content is organized as a set of categorized documents. For example::

        blog/
            2019/
                01-31. first_article_of_the_year.adoc
                12-31. last_article_of_the_year.adoc

    As part of website's content update, every document is loaded, processed,
    and finally stored, updated or deleted in the database.

    :param directory:
        path of the directory where website's content is stored.
    :param reader:
        function to read (and convert on the fly) documents.
    :param prompt:
        function to interactively ask questions during documents processing,
        when certain things cannot be completely done automatically.
    """

    directory: Path
    handlers: Mapping[str, 'BaseDocumentHandler']
    reader: Callable = open
    prompt: Callable = input

    def update(self, changes: Mapping[str, Iterable[Path]]) -> List[Document]:
        """Update documents in database.

        :param changes:
            source file paths of ``added``, ``modified``, ``renamed`` and
            ``deleted`` document.

        :raise ~.ItemAlreadyExisting:
            when trying to create documents already existing in database.
        :raise ~.ItemNotFound:
            when trying to modify documents not existing in database.
        :raise ~.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.

        :return:
            newly created or updated documents.
        """
        added = self.add(changes['added'])
        modified = self.refresh(changes['modified'])
        renamed = self.rename(changes['renamed'])

        self.delete(changes['deleted'])

        return added + modified + renamed

    def add(self, new: Iterable[Path]) -> List[Document]:
        """Insert new documents into database.

        :param new:
            paths of documents source files.

        :raise ~.ItemAlreadyExisting:
            if a document already exists in database.
        :raise ~.HandlerNotFound:
            if a document doesn't have any handler defined in :attr:`handlers`.
        :raise ~.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.

        :return:
            newly created documents.
        """
        documents = []

        for src in new:
            # Can raise:
            # HandlerNotFound, ItemAlreadyExisting, InvalidDocumentLocation.
            document = self.get_handler(src).insert()
            documents.append(document)

        return documents

    def refresh(self, existing: Iterable[Path]) -> List[Document]:
        """Update existing documents in database.

        :param existing:
            paths of documents source files.

        :raise ~.ItemNotFound:
            if a document doesn't exist in database.
        :raise ~.HandlerNotFound:
            if a document doesn't have any handler defined in :attr:`handlers`.
        :raise ~.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.

        :return:
            updated documents.
        """
        documents = []

        for src in existing:
            # Can raise HandlerNotFound, ItemNotFound, InvalidDocumentLocation.
            document = self.get_handler(src).update()
            documents.append(document)

        return documents

    def rename(self, existing: Iterable[Tuple[Path, Path]]) -> List[Document]:
        """Rename and update existing documents in database.

        :param existing:
            previous and new paths of documents source files.

        :raise ~.ItemNotFound:
            if a document doesn't exist in database.
        :raise ~.HandlerNotFound:
            if a document doesn't have any handler defined in :attr:`handlers`.
        :raise ~.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.

        :return:
            updated documents.
        """
        documents = []

        for src, dst in existing:
            # Can raise HandlerNotFound or ItemNotFound.
            src_handler = self.get_handler(src)
            dst_handler = self.get_handler(dst)

            try:
                assert src_handler.__class__ is dst_handler.__class__
            except AssertionError:
                raise exceptions.DocumentCategoryChanged(src, dst)

            document = src_handler.rename(dst)  # Can raise ItemNotFound
            documents.append(document)

        return documents

    def delete(self, removed: Iterable[Path]) -> None:
        """Delete documents from database.

        :param removed:
            paths of documents source files.

        :raise ~.ItemNotFound:
            if a document doesn't exist in database.
        :raise ~.HandlerNotFound:
            if a document doesn't have any handler defined in :attr:`handlers`.
        :raise ~.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.
        """
        for src in removed:
            # Can raise HandlerNotFound, ItemNotFound, InvalidDocumentLocation.
            self.get_handler(src).delete()

    # Helpers

    def get_handler(self, document: Union[Path, PurePath]) -> 'BaseDocumentHandler':  # noqa: E501
        """Return handler to process the source file of a document.

        :param document:
            path of the document's source file.

        :raise ~.HandlerNotFound:
            if no handler in :attr:`handlers` is defined
            for this type of document.
        :raise ~.InvalidDocumentLocation:
            when the source file is not located in :attr:`directory`
            or inside a subdirectory.
        """
        if document.is_absolute():
            try:
                relative_path = document.relative_to(self.directory)
            except ValueError:
                raise exceptions.InvalidDocumentLocation(document)
        else:
            relative_path = document

        try:
            category = list(relative_path.parents)[::-1][1].name
            handler = self.handlers[category]
        except IndexError:
            raise exceptions.DocumentNotCategorized(document)
        except KeyError:
            raise exceptions.HandlerNotFound(document)

        return handler(document, self.reader, self.prompt)


# Document Processing

@dataclass
class BaseDocumentHandler(ABC):
    """Manage the life cycle of a document in database.

    :param path:
        path of the document's source file. Every document must be written in
        HTML, and respect a naming convention. See documentation of handler
        subclasses for more info.
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
            URI the document currently has in database. If not provided, the
            URI will be retrieved from the document's :attr:`path`.
        :param create:
            create the document if it doesn't exist yet in database.
        :return:
            the updated (or newly created) document.

        :raise ~.ItemNotFound:
            if the document cannot be found, and ``create`` is set to ``False``.
        :raise ~.ItemAlreadyExisting:
            if ``create`` is set to ``True``, but the document already exists.
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
    # Always process paths from right to left,
    # to be able to process absolute or relative paths.

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

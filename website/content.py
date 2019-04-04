"""Main entry point to manage content of my website."""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path, PurePath
from typing import (
    Callable, ClassVar, Dict, Iterable, List, Mapping, Tuple, Union)

import aiofiles
import lxml.etree
import lxml.html
from lxml.cssselect import CSSSelector

from website import exceptions
from website.blog.models import Category, Tag
from website.models import Document
from website.update import (
    AsyncShellPrompt, BaseUpdateRunner, BaseUpdateManager)
from website.utils import BaseCommandLine
from website.utils.git import Repository

DocumentPath = Union[Path, PurePath]  # For prod and tests

logger = logging.getLogger(__name__)


class ContentUpdateRunner(BaseUpdateRunner):

    def __init__(self, from_commit: str, to_commit: str, **kwargs):
        BaseUpdateRunner.__init__(self, **kwargs)
        self.from_commit = from_commit
        self.to_commit = to_commit

    def plan(self) -> Dict[str, List[Path]]:
        diff = self.manager.repository.diff(self.from_commit, self.to_commit)
        return {
            'to_add': diff['added'],
            'to_replace': diff['replaced'],
            'to_rename': diff['renamed'],
            'to_delete': diff['deleted'],
        }

    async def proceed(self) -> List[Document]:
        """
        :raise ~.ItemAlreadyExisting:
            when trying to create documents already existing in database.
        :raise ~.ItemNotFound:
            when trying to modify documents not existing in database.
        :raise ~.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.
        """
        added = await self.manager.add(self.todo['to_add'])
        replaced = await self.manager.replace(self.todo['to_replace'])
        renamed = await self.manager.rename(self.todo['to_rename'])

        self.delete(self.todo['to_delete'])

        return [added + replaced + renamed]

    def generate_preview(self) -> str:
        """Print a Git diff.

        quiet: bool = True, output: TextIO = sys.stdout

        :param diff: pretty version of a diff, as returned by :meth:`diff`.
        :param output: text stream to print the diff.

        :param quiet: prints changes on ``output`` if set to ``False``.
        :param output: text stream to use for printing.
        """
        output = StringIO()

        for action, files in self.todo:
            if files:
                print(f"The following files have been {action}:", file=output)

                for f in files:
                    if isinstance(f, tuple):
                        # - src_file -> dst_file
                        print("- ", end="", file=output)
                        print(*f, sep=" -> ", file=output)
                    else:
                        print(f"- {f}", file=output)

        return output


# TODO: Add handlers to docstring (03/2019)
class ContentUpdateManager(BaseUpdateManager):
    """Manage website's content life cycle.

    The content is organized as a set of categorized documents. For example::

        blog/
            2019/
                01-31. first_article_of_the_year.adoc
                12-31. last_article_of_the_year.adoc

    As part of website's content update, every document is loaded, processed,
    and finally stored, updated or deleted in the database.

    :param repository:
        path of the Git repository where website's content is stored.
    :param reader:
        function to read (and convert on the fly) documents.
    :param prompt:
        function to interactively ask questions during documents processing,
        when certain things cannot be completely done automatically.
    """

    runner = ContentUpdateRunner

    def __init__(
            self,
            repository: Repository,
            handlers: Mapping[str, 'BaseDocumentHandler'], *,
            reader: Callable = aiofiles.open,
            prompt: 'WebsiteContentPrompt' = None):

        self.repository = repository
        self.handlers = handlers
        self.reader = reader
        self.prompt = prompt or WebsiteContentPrompt()

    # Main API

    # TODO: Update docstring (03/2019)
    def update(self, from_commit: str, to_commit: str = 'HEAD'):
        """...

        :param repository:
            Git repository where website's content is stored.
        """
        return ContentUpdateRunner(from_commit, to_commit, manager=self)

    # TODO: Update docstring (03/2019)
    async def add(self, new: Iterable[Path], *, batch=False) -> List[Document]:
        """Manually insert specific new documents into database.

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
        return asyncio.gather(
            self.get_handler(src).insert(batch=batch) for src in new)

    # TODO: Update docstring (03/2019)
    async def replace(self, existing: Iterable[Path], *, batch=False) -> List[Document]:
        """Manually update specific existing documents in database.

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
        return await asyncio.gather(
            self.get_handler(src).update(batch=batch) for src in new)

    # TODO: Update docstring (03/2019)
    async def rename(self, existing: Iterable[Tuple[Path, Path]], *, batch=False) -> List[Document]:
        """Manually rename and update specific existing documents in database.

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
        tasks = []

        for src, dst in existing:
            # Can raise HandlerNotFound or ItemNotFound.
            src_handler = self.get_handler(src)
            dst_handler = self.get_handler(dst)

            try:
                assert src_handler.__class__ is dst_handler.__class__
            except AssertionError:
                raise exceptions.DocumentCategoryChanged(src, dst)

            # Can raise ItemNotFound.
            task = src_handler.rename(dst, batch=batch)
            tasks.append(task)

        return await asyncio.gather(*tasks)

    def delete(self, removed: Iterable[PurePath]) -> None:
        """Manually delete specific documents from database.

        :param removed:
            paths of deleted documents source files.

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
                relative_path = document.relative_to(self.repository.path)
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


class WebsiteContentPrompt(AsyncShellPrompt):
    @property
    def questions(self):
        return {
            Category.name: (
                'Please enter a name for the new "{uri}" category: '),
            Tag.name: (
                'Please enter a name for the new "{uri}" tag: '),
        }


# Document Processing

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

    #: Document model clas.
    model: ClassVar[Document]
    #: Document parser class.
    parser: ClassVar['BaseDocumentSourceParser']

    def __init__(
            self, path: DocumentPath, *,
            reader: Callable = aiofiles.open, prompt: AsyncShellPrompt = None):
        self.path = path
        self.reader = reader
        self.prompt = prompt or WebsiteContentPrompt()

        self._document = None  # Used for caching purpose
        self._source = None  # Used for caching purpose

    @property
    def document(self) -> Document:
        """Look for the document in database.

        :raise ~.ItemNotFound: if the document cannot be found.
        """
        if not self._document:
            uri = self.scan_uri()
            self._document = self.model.find(uri=uri)  # Can raise ItemNotFound

        return self._document

    @document.setter
    def document(self, value: Document):
        self._document = value

    @property
    async def source(self) -> 'BaseDocumentSourceParser':
        """Load document's source on the fly.

        :raise ~.DocumentLoadingError:
            when something wrong happens while reading the source file.
        """
        if not self._source:
            self._source = await self.load()  # Can raise DocumentLoadingError

        return self._source

    # Main API

    async def insert(self, *, batch: bool = False) -> Document:
        """Insert document into database.

        :param batch:
            set to ``True`` to delay some actions requiring user input.
            Useful when several documents are processed in parallel.
        :return:
            the newly created document.
        :raise ~.ItemAlreadyExisting:
            if a conflict happens during document insertion.
        """
        # Can raise ItemAlreadyExisting.
        return await self.update(create=True, batch=batch)

    # TODO: Update docstring (03/2019)
    async def update(
            self, uri: str = None, create: bool = False, *,
            batch: bool = False) -> Document:
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

            self.document = document

        elif uri:  # Renaming
            self.document = self.model.find(uri=uri)  # Can raise ItemNotFound
            self.document.uri = self.scan_uri()  # New URI

        await self.process(batch=batch)

        if not batch:
            # Batch operations can create transient documents.
            # Saving them could raise integrity errors from the database.
            self.document.save()

        if create:
            message = "Created new %s: %s"
            logger.info(message, self.document.doc_type, self.document.uri)
        elif uri:
            message = "Renamed and updated existing %s: %s"
            logger.info(message, self.document.doc_type, self.document.uri)
        else:
            message = "Updated existing %s: %s"
            logger.info(message, self.document.doc_type, self.document.uri)

        return self.document

    async def rename(self, target: Path, *, batch: bool = False) -> Document:
        """Rename (and update) document in database.

        :param target: the new path of document's source file.
        :return: the updated and renamed document.
        :raise ~.ItemNotFound: if the document doesn't exist.
        """
        # TODO: Set-up an HTTP redirection (01/2019)
        uri = self.scan_uri()
        handler = self.__class__(target, reader=self.reader, prompt=self.prompt)  # noqa: E501
        return await handler.update(uri, batch=batch)

    def delete(self) -> None:
        """Remove a document from database.

        :return: URI of the deleted document.
        :raise ~.ItemNotFound: if the document doesn't exist.
        """
        uri = self.document.uri
        doc_type = self.document.doc_type

        self.document.delete()  # Can raise ItemNotFound
        logger.info("Deleted %s: %s", doc_type, uri)

    # Helpers

    async def load(self) -> 'BaseDocumentSourceParser':
        """Read and prepare for parsing the source file located at :attr:`path`.

        :raise ~.DocumentLoadingError:
            when something wrong happens while reading the source file
            (e.g., file not found or unsupported format).
        """  # noqa: E501
        try:
            async with self.reader(self.path) as source_file:
                source = await source_file.read()
        except (OSError, UnicodeDecodeError) as exc:
            raise exceptions.DocumentLoadingError(self, exc)

        return self.parser(source)

    @abstractmethod
    async def process(self, *, batch: bool = False) -> None:
        """Parse :attr:`path` and update :attr:`document`'s attributes.

        :param batch:
            set to ``True`` to delay some actions requiring user input.
            Useful when several documents are processed in parallel.
        """

    # Path Scanners
    # Always process paths from right to left,
    # to be able to handle absolute or relative paths.

    def scan_uri(self) -> str:
        """Return document's URI, based on its :attr:`path`."""
        return self.path.stem.split('.')[-1]


class BaseDocumentSourceParser:
    """Parse HTML source of a document.

    :raise ~.DocumentMalformatted: when the given source is not valid HTML.
    """  # noqa: E501

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

class BaseDocumentReader(ABC, BaseCommandLine):
    """Base class for external document readers.

    Provides a subset of :func:`aiofiles.open`'s API.

    Every reader relies on a :attr:`~program` installed locally, to open, read
    and if necessary convert documents on the fly to HTML format. The result of
    the conversion should be displayed on the standard output.

    :param shell:
        alternative shell to run the reader's :attr:`~program`. Must have a
        similar API to :func:`asyncio.create_subprocess_shell`.
    """

    #: Name of the reader's binary to execute for reading documents.
    program: ClassVar[str] = None
    #: Default arguments to use when running the reader's program.
    arguments: ClassVar[str] = None

    def __init__(self, shell: Callable = None):
        BaseCommandLine.__init__(self, shell)

        #: Path of the document to read. Set by :meth:`__call__`.
        self.path = None

    def __call__(self, path: Union[str, Path]) -> 'DocumentOpener':
        """Open the document for further reading.

        Can be called directly or used as a context manager.

        :raise FileNotFoundError: when the document cannot be opened.
        """
        path = Path(path)

        if not path.is_file():
            raise FileNotFoundError(f"Document doesn't exist: {path}")

        self.path = Path(path)
        return DocumentOpener(self)

    async def read(self) -> str:
        """Read and convert to HTML the document located at :attr:`path`.

        :raise OSError:
            if the reader's :attr:`~program` cannot convert the document.
        :raise UnicodeDecodeError:
            when the conversion's result is invalid.
        """
        assert self.path is not None, "Open a file before trying to read it"

        cmdline = self.arguments.format(path=self.path)
        # Can raise OSError or UnicodeDecodeError.
        html = await self.run(cmdline)

        return html.strip()


@dataclass
class DocumentOpener(AbstractAsyncContextManager):
    """Helper for :class:`BaseDocumentReader` to open documents.

    :param reader: reader instance opening the document.
    """

    reader: BaseDocumentReader

    def __getattr__(self, name: str):
        """Let :attr:`reader` opening a document as a function call."""
        return getattr(self.reader, name)

    async def __aenter__(self) -> BaseDocumentReader:
        """Let :attr:`reader` opening a document inside a context manager."""
        return self.reader

    async def __aexit__(self, *exc) -> None:
        """Nothing done here for the moment..."""
        return

"""Base classes to process website's source files."""

from abc import ABC, abstractmethod, abstractproperty
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, Iterable, List, Optional

import aiofiles
import lxml.html

from website import exceptions
from website.base.models import BaseDocument
from website.base.parsers import BaseDocumentSourceParser
from website.models import Category, Tag


class CatchProcessingErrors(type):
    """Meta-class used by all document processors.

    Catch errors automatically when calling processing or scanning methods
    (i.e., methods starting with ``process_`` or ``scan_``).

    This allows to process a document all at once, without having to bother with
    multiple try-catch blocks.
    """

    def __new__(meta, classname, supers, classdict):  # noqa: D102, N804

        def catch_processing_errors(func):
            async def wrapper(self, *args, **kwargs):
                try:
                    return await func(self, *args, **kwargs)
                except (exceptions.DocumentProcessingError, exceptions.DocumentParsingError) as exc:  # noqa: E501
                    if not self._catch_errors:
                        raise

                    self._errors.add(exc)

            return wrapper

        def catch_scanning_errors(func):
            def wrapper(self, *args, **kwargs):
                try:
                    return func(self, *args, **kwargs)
                except exceptions.DocumentPathScanningError as exc:
                    if not self._catch_errors:
                        raise

                    self._errors.add(exc)

            return wrapper

        for attr, attrval in classdict.items():
            if attr.startswith('process_'):
                classdict[attr] = catch_processing_errors(attrval)

            elif attr.startswith('scan_'):
                classdict[attr] = catch_scanning_errors(attrval)

        return type.__new__(meta, classname, supers, classdict)


class BaseDocumentFileProcessor(metaclass=CatchProcessingErrors):
    """Process document's source to prepare it for later insertion in database.

    :param path:
        document's source file path.
    :param reader:
        function to read document's source file.
        Must have an API similar to :func:`open`.
        Can be used to convert on the fly a source file to HTML format for example.
    """

    #: Document parser class.
    parser: ClassVar[BaseDocumentSourceParser]

    def __init__(self, path: Path, *, reader: Callable = aiofiles.open):
        self.path = path
        self.reader = reader

        self._source = None  # To cache document's source
        self._errors = set()  # To store document's processing/parsing errors

        # To catch potential exceptions when processing the document.
        self._catch_errors = False

    @abstractmethod
    async def process(self) -> Dict[str, Any]:
        """Analyze document's source file.

        :return: document's attributes, as defined in document's model.
        """

    # Path Scanners
    # Always process paths from right to left,
    # to be able to handle absolute or relative paths.

    def scan_uri(self) -> str:
        """Return document's URI, based on its :attr:`path`."""
        return self.path.stem.split('.')[-1]

    # Processors

    async def process_category(self) -> Optional[Category]:
        """Parse and return document's category.

        :raise website.exceptions.DocumentCategoryMissing:
            if document's category is not defined in document's source.
        :raise website.exceptions.DocumentCategoryNotFound:
            if document's category is not found in database.
        """
        source = await self.load()

        if uri := source.parse_category():  # Can raise DocumentCategoryMissing
            try:
                return Category.find(uri=uri)
            except exceptions.ItemNotFound:
                raise exceptions.DocumentCategoryNotFound(uri)

    async def process_tags(self) -> Optional[List[Tag]]:
        """Parse and return document's tags.

        :raise website.exceptions.DocumentTagsNotFound:
            if some document's tags are not found in database.
        """
        source = await self.load()
        uris = set(source.parse_tags())

        tags = Tag.filter(uri=uris)
        unexisting_tags = uris - set(t.uri for t in tags)

        if unexisting_tags:
            raise exceptions.DocumentTagsNotFound(unexisting_tags)

        return sorted(tags)

    # Helpers

    @contextmanager
    def catch_processing_errors(self):
        """Catch potential errors when processing document's source file.

        Can be used as follows::

            source_file = BaseDocumentFileProcessor(file_path)

            with source_file.catch_processing_errors() as errors:
                source_file.process()
                print(errors)
        """
        try:
            self._catch_errors = True
            yield self._errors
        finally:
            self._catch_errors = False
            self._errors = set()

    async def load(self) -> lxml.html.HtmlElement:
        """Read and prepare for parsing the source file located at :attr:`path`.

        :raise website.exceptions.DocumentLoadingError:
            when something wrong happens while reading the source file
            (e.g., file not found or unsupported format).
        """
        if not self._source:
            try:
                async with self.reader(self.path) as source_file:
                    content = await source_file.read()
            except (OSError, UnicodeDecodeError) as exc:
                raise exceptions.DocumentLoadingError(self, exc)

            self._source = self.parser(content)

        return self._source

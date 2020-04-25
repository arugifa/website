"""Base classes to process website's source files."""

import logging
from abc import abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Optional, Tuple

import aiofiles
from arugifa.cms import exceptions as cms_errors
from arugifa.cms.processors import BaseFileProcessor
from arugifa.cms.typing import FileProcessingErrors, FileProcessingResult

from website import exceptions
from website.base import parsers
from website.models import Category, Tag
from website.typing import Document

logger = logging.getLogger(__name__)


class BaseDocumentFileProcessor(BaseFileProcessor):
    """Process document's source to prepare it for later insertion in database.

    :param path:
        document's source file path.
    :param reader:
        function to read document's source file.
        Must have an API similar to :func:`open`.
        Can be used to convert on the fly a source file to HTML format for example.
    """

    parser = ClassVar[parsers.BaseDocumentFileParser]
    model = ClassVar[Document]

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


class BaseMetadataFileProcessor(BaseFileProcessor):
    parser = ClassVar[parsers.BaseMetadataFileParser]

    async def process(self) -> Dict:
        source = await self.load()  # Can raise FileLoadingError

        with source.collect_errors() as errors:
            result = source.parse_items()

        if errors:
            raise cms_errors.InvalidFile(errors)

        return result

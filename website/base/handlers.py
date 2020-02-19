"""Base classes to manage content life cycle in database."""

import logging
from abc import ABC
from pathlib import Path, PurePath
from typing import Callable, ClassVar, Union

import aiofiles

from website import exceptions
from website.base.models import BaseDocument
from website.base.processors import BaseDocumentFileProcessor

DocumentPath = Union[Path, PurePath]  # For prod and tests

logger = logging.getLogger(__name__)


class BaseDocumentFileHandler(ABC):
    """Manage the life cycle of a document in database.

    :param path:
        path of the document's source file. Every document must be written in HTML,
        and respect a naming convention. See documentation of handler subclasses
        for more info.
    :param reader:
        function to read the documents.
    """

    #: Document model class.
    model: ClassVar[BaseDocument]
    #: Document processor class.
    processor: ClassVar[BaseDocumentFileProcessor]

    def __init__(self, path: DocumentPath, *, reader: Callable = aiofiles.open):
        #: Processor to analyze document's source file.
        self.source_file = self.processor(path, reader=reader)

        self.logger = CustomAdapter(logger, {'source_file': self.source_file.path})

    # Main API

    async def insert(self) -> BaseDocument:
        """Insert document into database.

        :return:
            the newly created document.

        :raise website.exceptions.ItemAlreadyExisting:
            if a conflict happens during document insertion.
        :raise website.exceptions.InvalidFile:
            if the document's source file is malformatted.
        """
        uri = self.source_file.scan_uri()
        document = self.model(uri=uri)

        if document.exists():
            raise exceptions.ItemAlreadyExisting(uri)

        processing, errors = await self.source_file.process()

        if errors:
            self.logger.error(f"Could not process file")
            raise exceptions.InvalidFile(self.source_file.path, errors)

        document.update(**processing)
        self.logger.info(f"Inserted document in database")

        return document

    async def update(self) -> BaseDocument:
        """Update document in database.

        :return:
            the updated document.

        :raise website.exceptions.ItemNotFound:
            if the document doesn't exist in database.
        :raise website.exceptions.InvalidFile:
            if the document's source file is malformatted.
        """
        document = self.look_in_db()  # Can raise ItemNotFound

        processing, errors = await self.source_file.process()

        if errors:
            self.logger.error("Could not process file")
            raise exceptions.InvalidFile(self.source_file.path, errors)

        document.update(**processing)
        self.logger.info(f"Updated document in database")

        return document

    async def rename(self, target: Path) -> BaseDocument:
        """Rename (and update) document in database.

        :param target:
            new path of document's source file.

        :return:
            the updated and renamed document.

        :raise website.exceptions.ItemNotFound:
            if the document doesn't exist in database.
        :raise website.exceptions.InvalidFile:
            if the document's source file is malformatted.
        """
        # TODO: Set-up an HTTP redirection (01/2019)
        document = self.look_in_db()  # Can raise ItemNotFound

        new_handler = self.__class__(target, reader=self.source_file.reader)
        new_uri = new_handler.source_file.scan_uri()

        document.update(uri=new_uri)
        self.logger.info(f"Renamed document in database to {document.uri}")

        return await new_handler.update()  # Can raise InvalidFile

    def delete(self) -> None:
        """Remove a document from database.

        :raise website.exceptions.ItemNotFound: if the document doesn't exist.
        """
        document = self.look_in_db()  # Can raise ItemNotFound
        document.delete()
        self.logger.info(f"Deleted document in database")

    # Helpers

    def look_in_db(self) -> BaseDocument:
        """Look for the document in database.

        :raise website.exceptions.ItemNotFound: if the document cannot be found.
        """
        uri = self.source_file.scan_uri()
        return self.model.find(uri=uri)  # Can raise ItemNotFound

"""Base classes to manage content life cycle in database."""

import logging
from pathlib import Path
from typing import ClassVar, List

from arugifa.cms import exceptions as cms_errors
from arugifa.cms.handlers import BaseFileHandler

from website import exceptions
from website.base import processors
from website.base.models import BaseDocument
from website.typing import Metadata

logger = logging.getLogger(__name__)


class BaseDocumentFileHandler(BaseFileHandler):
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
    processor: ClassVar[processors.BaseDocumentFileProcessor]

    # Main API

    async def insert(self) -> BaseDocument:
        """Insert document into database.

        :return:
            the newly created document.

        :raise website.exceptions.DupplicatedContent:
            if a conflict happens during document insertion.
        :raise website.exceptions.InvalidFile:
            if the document's source file is malformatted.
        """
        uri = self.source_file.scan_uri()
        document = self.model(uri=uri)

        if document.exists():
            raise exceptions.DupplicatedContent(uri)

        # TODO: Raise InvalidFile inside process() instead? +1 (04/2020)
        processing, errors = await self.source_file.process()

        if errors:
            logger.error(f"Could not process file")
            raise cms_errors.InvalidFile(errors)

        document.update(**processing)
        logger.info(f"Inserted document in database")

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
            logger.error("Could not process file")
            raise cms_errors.InvalidFile(errors)

        document.update(**processing)
        logger.info(f"Updated document in database")

        return document

    async def rename(self, target: Path) -> 'BaseDocumentFileHandler':
        """Rename document in database.

        :param target:
            new path of document's source file.

        :return:
            the renamed document. NOT TRUE ANYMORE!

        :raise website.exceptions.ItemNotFound:
            if the document doesn't exist in database.
        :raise website.exceptions.InvalidFile:
            if the document's source file is malformatted.
        """
        # TODO: Set-up an HTTP redirection (01/2019)
        document = self.look_in_db()  # Can raise ItemNotFound

        new_handler = self.__class__(target, reader=self.source_file.reader)
        # TODO: Test error because target doesn't belong to handler (04/2020)
        new_uri = new_handler.source_file.scan_uri()

        document.update(uri=new_uri)
        logger.info(f"Renamed document in database to {document.uri}")

        return new_handler

    def delete(self) -> None:
        """Remove a document from database.

        :raise website.exceptions.ItemNotFound: if the document doesn't exist.
        """
        document = self.look_in_db()  # Can raise ItemNotFound
        document.delete()
        logger.info(f"Deleted document in database")

    # Helpers

    def look_in_db(self) -> BaseDocument:
        """Look for the document in database.

        :raise website.exceptions.ItemNotFound: if the document cannot be found.
        """
        uri = self.source_file.scan_uri()
        return self.model.find(uri=uri)  # Can raise ItemNotFound


class BaseMetadataFileHandler(BaseFileHandler):
    model: ClassVar[Metadata]
    processor: ClassVar[processors.BaseMetadataFileProcessor]

    async def insert(self) -> List[Metadata]:
        new = []
        existing = []

        processing = await self.source_file.process()  # Can raise InvalidFile

        for uri, name in processing.items():
            item = self.model(uri=uri, name=name)

            if item.exists():
                existing.append(uri)
            else:
                item.save()
                new.append(item)

        if existing:
            raise cms_errors.DupplicatedContent(*existing)

        return new

    async def update(self) -> List[Metadata]:
        existing = {item.uri: item for item in self.model.all()}
        updated = []

        new = await self.source_file.process()

        for uri, name in new.items():
            try:
                item = existing.pop(uri)
            except KeyError:
                item = self.model(uri=uri, name=name)
            else:
                item.name = name
            finally:
                item.save()
                updated.append(item)

        for item in existing.values():
            item.delete()

        return updated

    async def rename(self, target: Path) -> 'BaseMetadataFileHandler':
        return self.__class__(target)

    async def delete(self) -> None:
        # TODO: What happens when deleting metadata still associated to documents? 4/20
        # Can raise DB Integrity Error?
        for item in self.model.all():
            item.delete()

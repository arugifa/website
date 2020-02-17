from abc import ABC, abstractmethod
from pathlib import PurePath
from typing import ClassVar

import pytest

from website import exceptions
from website.base.factories import BaseDocumentFactory
from website.base.handlers import BaseDocumentFileHandler


class BaseDocumentFileHandlerTest(ABC):
    handler: ClassVar[BaseDocumentFileHandler] = None  # Handler class to test
    factory: ClassVar[BaseDocumentFactory] = None  # Factory to generate documents

    # Look in database.

    def test_look_for_document_in_db(self, db):
        source_file = PurePath('to_look_for.html')
        handler = self.handler(source_file)

        expected = self.factory(uri='to_look_for')
        actual = handler.look_in_db()

        assert actual == expected

    def test_look_for_unexisting_document_in_db(self, db):
        source_file = PurePath('unexisting.html')
        handler = self.handler(source_file)

        with pytest.raises(exceptions.ItemNotFound):
            handler.look_in_db()

    # Insert document.

    @abstractmethod
    async def test_insert_document(self, db):
        pass

    async def test_insert_already_existing_document(self, db):
        source_file = PurePath('existing.html')
        self.factory(uri='existing')

        with pytest.raises(exceptions.ItemAlreadyExisting):
            await self.handler(source_file).insert()

    async def test_insert_malformatted_document(self, db, tmp_path):
        source_file = tmp_path / 'malformatted.html'
        source_file.write_text("Malformatted document")

        with pytest.raises(exceptions.InvalidFile):
            await self.handler(source_file).insert()

    # Update document.

    @abstractmethod
    async def test_update_document(self, db):
        pass

    async def test_update_not_existing_document(self, db):
        source_file = PurePath('missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            await self.handler(source_file).update()

    async def test_update_malformatted_document(self, db, tmp_path):
        source_file = tmp_path / 'malformatted.html'
        source_file.write_text("Malformatted document")

        self.factory(uri='malformatted')

        with pytest.raises(exceptions.InvalidFile):
            await self.handler(source_file).update()

    # Rename document.

    @abstractmethod
    async def test_rename_document(self, db):
        pass

    async def test_rename_not_existing_document(self, db):
        source_file = PurePath('missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            await self.handler(source_file).rename('new_name')

    async def test_rename_malformatted_document(self, db, tmp_path):
        source_file = tmp_path / 'malformatted.html'
        source_file.write_text("Malformatted document")

        self.factory(uri='malformatted')

        with pytest.raises(exceptions.InvalidFile):
            await self.handler(source_file).update()

    # Delete document.

    @abstractmethod
    def test_delete_document(self, db):
        pass

    def test_delete_not_existing_document(self, db):
        source_file = PurePath('missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            self.handler(source_file).delete()

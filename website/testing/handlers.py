from pathlib import Path, PurePath
from textwrap import dedent
from typing import ClassVar

import pytest
from arugifa.cms import exceptions as cms_errors
from arugifa.cms.testing.handlers import BaseFileHandlerTest

from website import exceptions
from website.base import factories, handlers, models


class BaseDocumentFileHandlerTest(BaseFileHandlerTest):
    handler: ClassVar[handlers.BaseDocumentFileHandler]  # Handler class to test
    factory: ClassVar[factories.BaseDocumentFactory]  # Factory to generate documents

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

    async def test_insert_already_existing_document(self, db):
        source_file = PurePath('existing.html')
        self.factory(uri='existing')

        with pytest.raises(exceptions.DupplicatedContent):
            await self.handler(source_file).insert()

    async def test_insert_malformatted_document(self, db, tmp_path):
        source_file = tmp_path / 'malformatted.html'
        source_file.write_text("Malformatted document")

        with pytest.raises(cms_errors.InvalidFile):
            await self.handler(source_file).insert()

    # Update document.

    async def test_update_not_existing_document(self, db):
        source_file = PurePath('missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            await self.handler(source_file).update()

    async def test_update_malformatted_document(self, db, tmp_path):
        source_file = tmp_path / 'malformatted.html'
        source_file.write_text("Malformatted document")

        self.factory(uri='malformatted')

        with pytest.raises(cms_errors.InvalidFile):
            await self.handler(source_file).update()

    # Rename document.

    async def test_rename_not_existing_document(self, db):
        source_file = PurePath('missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            await self.handler(source_file).rename('new_name')

    async def test_rename_malformatted_document(self, db, tmp_path):
        source_file = tmp_path / 'malformatted.html'
        source_file.write_text("Malformatted document")

        self.factory(uri='malformatted')

        with pytest.raises(cms_errors.InvalidFile):
            await self.handler(source_file).update()

    # Delete document.

    def test_delete_not_existing_document(self, db):
        source_file = PurePath('missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            self.handler(source_file).delete()


class BaseMetadataFileHandlerTest:
    processor: ClassVar[handlers.BaseMetadataFileHandler]
    model: ClassVar[models.BaseMetadataModel]
    factory: ClassVar[factories.BaseMetadataFactory]

    @pytest.fixture
    def source_file(self, tmp_path):
        source_file = tmp_path / 'metadata.yml'
        source_file.write_text(dedent("""
            house: House Music
            trance: Trance Music
        """))
        return source_file

    def assert_metadata_has_been_saved(self, metadata):
        assert len(metadata) == 2
        assert self.model.all() == metadata

        assert metadata[0].uri == 'house'
        assert metadata[0].name == "House Music"
        assert metadata[1].uri == 'trance'
        assert metadata[1].name == "Trance Music"

    # Insert metadata.

    async def test_insert_new_metadata(self, db, source_file):
        metadata = await self.handler(source_file).insert()
        self.assert_metadata_has_been_saved(metadata)

    async def test_insert_existing_metadata(self, db, source_file):
        for uri in ['house', 'trance']:
            self.factory(uri=uri)

        with pytest.raises(cms_errors.DupplicatedContent):
            await self.handler(source_file).insert()

    # Update metadata.

    async def test_update_existing_metadata(self, db, source_file):
        expected = [
            self.factory(uri='house', name="House Musique"),
            self.factory(uri='trance', name="Trance Musique"),
        ]

        actual = await self.handler(source_file).update()

        assert actual == expected
        self.assert_metadata_has_been_saved(actual)

    async def test_update_new_metadata(self, db, source_file):
        self.factory(uri='house', name="House Music")
        metadata = await self.handler(source_file).update()
        self.assert_metadata_has_been_saved(metadata)

    async def test_update_deleted_metadata(self, db, source_file):
        expected = [
            self.factory(uri='house', name="House Music"),
            self.factory(uri='trance', name="Trance Music"),
        ]
        self.factory(uri='gabber', name="Gabber Music")

        actual = await self.handler(source_file).update()

        assert actual == expected
        self.assert_metadata_has_been_saved(actual)

    # Rename metadata.

    async def test_rename_metadata(self, source_file):
        handler = self.handler(source_file)
        assert handler.source_file.path == source_file

        new_path = Path('/new/location/meta.yml')
        new_handler = await handler.rename(new_path)
        assert new_handler.source_file.path == new_path

    # Delete metadata.

    async def test_delete_metadata(self, db):
        source_file = PurePath('/random/location/meta.yml')

        self.factory.create_batch(2)
        assert len(self.model.all()) == 2

        await self.handler(source_file).delete()
        assert len(self.model.all()) == 0

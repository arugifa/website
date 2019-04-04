import gzip
from abc import ABC, abstractmethod
from hashlib import sha1
from pathlib import PurePath
from typing import ClassVar

import pytest

from website import exceptions
from website.content import (
    BaseDocumentHandler, BaseDocumentReader, BaseDocumentSourceParser)
from website.models import Document

from tests.utils._test_utils import BaseCommandLineTest  # noqa: I100


class BaseDocumentHandlerTest(ABC):
    handler: ClassVar[BaseDocumentHandler] = None  # Handler class to test
    factory: ClassVar[Document] = None  # Factory to generate documents

    # Insert document.

    @abstractmethod
    async def test_insert_document(self, db, fixtures, prompt):
        pass

    @abstractmethod
    async def test_insert_already_existing_document(self, db, fixtures):
        pass

    @abstractmethod
    async def test_insert_documents_in_batch(self, db, fixtures, prompt):
        pass

    # Update document.

    @abstractmethod
    async def test_update_document(self, db, fixtures, prompt):
        pass

    @abstractmethod
    async def test_update_not_existing_document(self, db, fixtures):
        pass

    @abstractmethod
    async def test_update_documents_in_batch(self, db, fixtures, prompt):
        pass

    # Rename document.

    @abstractmethod
    async def test_rename_document(self, db, fixtures, prompt):
        pass

    @abstractmethod
    async def test_rename_not_existing_document(self, db, fixtures):
        pass

    @abstractmethod
    async def test_rename_documents_in_batch(self, db, fixtures, prompt):
        pass

    # Delete document.

    @abstractmethod
    def test_delete_document(self, db):
        pass

    @abstractmethod
    def test_delete_not_existing_document(self, db):
        pass

    # Get document.

    async def test_document_is_automatically_retrieved(self, db, tmp_path):
        document = self.factory(uri='document')
        source_file = tmp_path / 'document.html'
        assert self.handler(source_file).document is document

    async def test_retrieve_not_existing_document(
            self, db, tmp_path):
        source_file = tmp_path / 'document.html'

        with pytest.raises(exceptions.ItemNotFound):
            assert self.handler(source_file).document

    # Get source.

    async def test_document_source_is_automatically_loaded(self, tmp_path):
        source_file = tmp_path / 'document.html'
        source_file.write_text("Hello, World!")

        parser = await self.handler(source_file).source
        assert parser.source.text_content() == "Hello, World!"

    async def test_load_not_existing_document_source(self, tmp_path):
        source_file = tmp_path / 'missing.html'

        with pytest.raises(exceptions.DocumentLoadingError):
            await self.handler(source_file).source

    # Load document.

    async def test_load_document(self, tmp_path):
        source_file = tmp_path / 'document.html'
        source_file.write_text("Hello, World!")

        parser = await self.handler(source_file).load()
        assert parser.source.text_content() == "Hello, World!"

    async def test_load_not_existing_document(self, tmp_path):
        source_file = tmp_path / 'missing.html'

        with pytest.raises(exceptions.DocumentLoadingError):
            await self.handler(source_file).load()

    async def test_load_not_supported_document_format(self, tmp_path):
        archive = tmp_path / 'document.html.gz'

        with gzip.open(str(archive), 'wb') as f:
            f.write(b'random content')

        with pytest.raises(exceptions.DocumentLoadingError):
            await self.handler(archive).load()

    # Scan URI.

    def test_scan_uri(self):
        source_file = PurePath('document.html')
        actual = self.handler(source_file).scan_uri()
        assert actual == 'document'


class BaseDocumentSourceParserTest:
    parser: ClassVar[BaseDocumentSourceParser] = None  # Handler class to test

    @pytest.fixture(scope='class')
    def base_source(self, fixtures):
        document = fixtures['document.html'].open().read()
        return self.parser(document)

    # Initialize parser.

    def test_source_must_be_valid_html(self):
        with pytest.raises(exceptions.DocumentMalformatted):
            self.parser('')

    # Parse title.

    def test_parse_title(self, base_source):
        title = base_source.parse_title()
        assert title == 'Standard Document'

    @pytest.mark.parametrize('html', [
        '<html></html>',
        '<html><title></title></html>',
    ])
    def test_parse_missing_title(self, html):
        with pytest.raises(exceptions.DocumentTitleMissing):
            self.parser(html).parse_title()

    # Parse tags.

    def test_parse_tags(self, base_source):
        tags = base_source.parse_tags()
        assert tags == ['asciidoctor', 'tests']

    @pytest.mark.parametrize('html', [
        '<html><head></head></html>',
        '<html><head><meta name="keywords"></head></html>',
    ])
    def test_parse_missing_tags(self, html):
        tags = self.parser(html).parse_tags()
        assert tags == []

    def test_parse_empty_tags(self):
        html = '<html><head><meta name="keywords" content=",,"></head></html>'
        tags = self.parser(html).parse_tags()
        assert tags == []

    def test_parse_tags_surrounded_by_spaces(self):
        html = (
            '<html><head>'
            '<meta name="keywords" content="tag1, tag2 , tag3">'
            '</head></html>'
        )
        tags = self.parser(html).parse_tags()
        assert tags == ['tag1', 'tag2', 'tag3']

    def test_parse_tags_not_surrounded_by_spaces(self):
        html = (
            '<html><head>'
            '<meta name="keywords" content="tag1,tag2,tag3">'
            '</head></html>'
        )
        tags = self.parser(html).parse_tags()
        assert tags == ['tag1', 'tag2', 'tag3']


class BaseDocumentReaderTest(BaseCommandLineTest):
    reader: ClassVar[BaseDocumentReader] = None  # Reader class to test

    @pytest.fixture
    def program_factory(self):
        return self.reader

    # Open document.

    def test_open_not_existing_file(self, tmp_path):
        source_file = tmp_path / 'missing.txt'

        with pytest.raises(FileNotFoundError):
            self.reader()(source_file)

    # Read document.

    async def test_error_happening_while_reading_document(
            self, shell, tmp_path):
        source_file = tmp_path / 'document.txt'
        source_file.touch()

        reader = self.reader(shell=shell)
        shell.result = ("Invalid document", 1)

        with pytest.raises(OSError) as excinfo:
            await reader(source_file).read()

        assert "Invalid document" in str(excinfo)

    async def test_cannot_decode_reader_output(self, shell, tmp_path):
        source_file = tmp_path / 'document.txt'
        source_file.touch()

        shell.result = sha1(b"Nich Gut!").digest()
        reader = self.reader(shell=shell)

        with pytest.raises(UnicodeDecodeError):
            await reader(source_file).read()

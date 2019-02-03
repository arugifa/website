import gzip
from abc import ABC, abstractmethod
from pathlib import PurePath
from typing import ClassVar

import pytest

from website import exceptions
from website.content import BaseDocumentHandler, BaseDocumentSourceParser


class BaseDocumentHandlerTest(ABC):
    handler: ClassVar[BaseDocumentHandler] = None  # Handler class to test

    # Insert document.

    @abstractmethod
    def test_insert_document(self, db, fixtures, prompt):
        pass

    @abstractmethod
    def test_insert_already_existing_document(self, db, fixtures):
        pass

    # Update document.

    @abstractmethod
    def test_update_document(self, db, fixtures, prompt):
        pass

    @abstractmethod
    def test_update_not_existing_document(self, db, fixtures):
        pass

    # Rename document.

    @abstractmethod
    def test_rename_document(self, db, fixtures, prompt):
        pass

    @abstractmethod
    def test_rename_not_existing_document(self, db, fixtures):
        pass

    # Delete document.

    @abstractmethod
    def test_delete_document(self, db):
        pass

    @abstractmethod
    def test_delete_not_existing_document(self, db):
        pass

    # Load document.

    def test_load_document(self, tmp_path):
        document = tmp_path / 'document.html'
        document.write_text("Hello, World!")

        parser = self.handler(document).load()
        assert parser.source.text_content() == "Hello, World!"

    def test_load_not_existing_document(self, tmp_path):
        document = tmp_path / 'void.html'

        with pytest.raises(exceptions.DocumentLoadingError):
            self.handler(document).load()

    def test_load_not_supported_document_format(self, tmp_path):
        archive = tmp_path / 'document.html.gz'

        with gzip.open(str(archive), 'wb') as f:
            f.write(b'random content')

        with pytest.raises(exceptions.DocumentLoadingError):
            self.handler(archive).load()

    # Scan URI.

    def test_scan_uri(self):
        path = PurePath('document.html')
        actual = self.handler(path).scan_uri()
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

import gzip
from abc import ABC, abstractmethod
from datetime import date
from pathlib import PurePath

import pytest

from website import exceptions
from website.content import BaseDocumentHandler, BaseDocumentSourceParser


class BaseDocumentHandlerTest(ABC):
    handler: BaseDocumentHandler = None  # Handler class to test

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

    def test_load_document_with_context_manager(self, tmp_path):
        document = tmp_path / 'document.html'
        document.write_text("Hello, World!")

        with self.handler(document).load() as parser:
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

    # Parse URI.

    def test_parse_document_uri(self):
        path = PurePath('document.html')
        actual = self.handler(path).scan_uri()
        assert actual == 'document'


class BaseDocumentSourceParserTest(ABC):
    parser: BaseDocumentSourceParser = None  # Handler class to test

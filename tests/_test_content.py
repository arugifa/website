import gzip
from abc import ABC, abstractmethod
from datetime import date
from pathlib import PurePath

import pytest

from website import exceptions
from website.content import BaseDocumentHandler


class BaseDocumentHandlerTest(ABC):
    handler: BaseDocumentHandler = None  # Handler class to test

    @abstractmethod
    def test_insert_document(self):
        pass

    @abstractmethod
    def test_update_document(self):
        pass

    @abstractmethod
    def test_rename_document(self):
        pass

    # Delete document.

    @abstractmethod
    def test_delete_document(self):
        pass

    @abstractmethod
    def test_delete_not_existing_document(self):
        pass

    # Read document.

    def test_read_document(self, tmp_path):
        document = tmp_path / 'article.txt'
        document.write_text("Hello, World!")

        content = self.handler(document).read()
        assert content == "Hello, World!"

    def test_read_not_existing_document(self, tmp_path):
        document = tmp_path / 'void.txt'

        with pytest.raises(exceptions.DocumentReadingError):
            self.handler(document).read()

    def test_read_not_supported_document_format(self, tmp_path):
        archive = tmp_path / 'archive.gz'

        with gzip.open(str(archive), 'wb') as f:
            f.write(b'random content')

        with pytest.raises(exceptions.DocumentReadingError):
            self.handler(archive).read()  # Not Unicode

    # Parse document's date.

    def test_parse_document_date(self):
        path = PurePath('blog/2018/04-08.article.txt')
        actual = self.handler(path).parse_date()
        assert actual == date(2018, 4, 8)

    def test_document_must_be_stored_inside_a_directory(self):
        path = PurePath('04-08.article.txt')
        with pytest.raises(ValueError):
            self.handler(path).parse_date()

    def test_document_directory_must_contain_year_number(self):
        path = PurePath('blog/invalid_year/04-08.article.txt')
        with pytest.raises(ValueError):
            self.handler(path).parse_date()

    @pytest.mark.parametrize('path', [
        'blog/2019/article.txt',
        'blog/2019/04.article.txt',
        'blog/2019/04-.article.txt',
        'blog/2019/john-doe.article.txt',
    ])
    def test_document_name_must_contain_month_and_day_numbers(self, path):
        path = PurePath(path)
        with pytest.raises(ValueError):
            self.handler(path).parse_date()

    # Parse document's URI.

    def test_parse_document_uri(self):
        path = PurePath('article.txt')
        actual = self.handler(path).parse_uri()
        assert actual == 'article'

    def test_get_uri_from_path_with_date(self):
        path = PurePath('04-08.article.txt')
        actual = self.handler(path).parse_uri()
        assert actual == 'article'

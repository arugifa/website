import gzip
from datetime import date
from pathlib import PurePath

import pytest

from website import exceptions
from website.blog.content import ArticleHandler


class BaseDocumentHandlerTest:
    handler = None  # Handler class to test

    # Document's Date

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

    # Document's URI

    def test_parse_document_uri(self):
        path = PurePath('article.txt')
        actual = self.handler(path).parse_uri()
        assert actual == 'article'

    def test_get_uri_from_path_with_date(self):
        path = PurePath('04-08.article.txt')
        actual = self.handler(path).parse_uri()
        assert actual == 'article'

    # Load Document

    def test_load_document(self, tmp_path):
        document = tmp_path / 'article.txt'
        document.write_text("Hello, World!")

        content = self.handler(document).read()
        assert content == "Hello, World!"

    def test_load_not_existing_document(self, tmp_path):
        document = tmp_path / 'void.txt'

        with pytest.raises(exceptions.DocumentReadingError):
            self.handler(document).read()

    def test_load_not_supported_document_format(self, tmp_path):
        archive = tmp_path / 'archive.gz'

        with gzip.open(str(archive), 'wb') as f:
            f.write(b'random content')

        with pytest.raises(exceptions.DocumentReadingError):
            self.handler(archive).read()  # Not Unicode


class TestArticleHandler(BaseDocumentHandlerTest):
    handler = ArticleHandler


"""

# Main API Tests

class BaseContentTest:
    func = None

    def test_no_callback_defined(self):
        callbacks = dict()
        paths = ['blog/article.txt']

        with pytest.raises(UpdateContentException) as excinfo:
            self.__class__.func(paths, callbacks)

        assert "Cannot find callback" in str(excinfo)

    def test_failed_to_process_document_with_callback(self, tmpdir):
        # Fixtures
        tmpdir.mkdir('blog').ensure('article.txt')
        paths = ['blog/article.txt']

        def callback(*args, **kwargs):
            raise Exception

        callbacks = {'blog': callback}

        # Test
        with tmpdir.as_cwd():
            with pytest.raises(UpdateContentException) as excinfo:
                self.__class__.func(paths, callbacks)

            assert "Failed to" in str(excinfo)


class BaseAddOrUpdateContentTest(BaseContentTest):
    def test_read_unexisting_file(self):
        callbacks = {'blog': (lambda: 'test')}
        paths = ['blog/article.txt']

        with pytest.raises(UpdateContentException) as excinfo:
            self.__class__.func(paths, callbacks)

        assert "Unable to read" in str(excinfo)


class TestInsertDocuments(BaseAddOrUpdateContentTest):
    func = content.insert_documents


class TestDeleteDocuments(BaseContentTest):
    func = content.insert_documents


class TestRenameDocuments(BaseAddOrUpdateContentTest):
    func = content.rename_documents


class TestUpdateDocuments(BaseAddOrUpdateContentTest):
    func = content.update_documents


# Helper Tests

class TestGetDocumentCallback:
    def test_get_callback(self):
        def expected():
            pass

        path = 'blog/article.txt'
        callbacks = {'blog': expected, 'notes': (lambda: 'test')}

        actual = content.get_document_callback(path, callbacks)
        assert actual is expected

    def test_unexisting_callback_raises_exception(self):
        path = 'notes/note.txt'
        callbacks = {'blog': (lambda: 'test')}

        with pytest.raises(KeyError):
            content.get_document_callback(path, callbacks)

    def test_cannot_get_callback_for_documents_without_category(self):
        path = 'article.txt'
        with pytest.raises(KeyError):
            content.get_document_callback(path, None)


class TestGetDocumentCategory:
    def get_category(self):
        path = 'notes/note.txt'
        actual = content.get_document_category(path)
        assert actual == 'notes'

    def test_get_category_from_path_with_date(self):
        path = 'blog/2018/04-08.article.txt'
        actual = content.get_document_category(path)
        assert actual == 'blog'

    def test_document_must_be_classified_in_a_directory(self):
        path = '04-08.article.txt'
        with pytest.raises(ValueError):
                content.get_document_category(path)

"""

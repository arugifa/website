from datetime import date

import pytest

from website import content
from website.exceptions import UpdateContentException


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


class TestGetDocumentDate:
    def test_get_date(self):
        path = 'blog/2018/04-08.article.txt'
        actual = content.get_document_date(path)
        assert actual == date(2018, 4, 8)

    def test_document_must_be_classified_in_a_directory(self):
        path = '04-08.article.txt'
        with pytest.raises(ValueError):
            content.get_document_date(path)

    def test_document_directory_must_contain_year_number(self):
        path = 'blog/test/04-08.article.txt'
        with pytest.raises(ValueError):
            content.get_document_date(path)

    def test_document_name_must_contain_month_and_day_numbers(self):
        path = 'blog/test/article.txt'
        with pytest.raises(ValueError):
            content.get_document_date(path)

        path = 'blog/test/04.article.txt'
        with pytest.raises(ValueError):
            content.get_document_date(path)

        path = 'blog/test/04-.article.txt'
        with pytest.raises(ValueError):
            content.get_document_date(path)

        path = 'blog/test/john-doe.article.txt'
        with pytest.raises(ValueError):
            content.get_document_date(path)


class TestGetDocumentURI:
    def test_get_uri(self):
        path = 'article.txt'
        actual = content.get_document_uri(path)
        assert actual == 'article'

    def test_get_uri_from_path_with_date(self):
        path = '04-08.article.txt'
        actual = content.get_document_uri(path)
        assert actual == 'article'

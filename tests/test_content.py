from pathlib import PurePath

import pytest

from website import exceptions
from website.content import BaseDocumentHandler, ContentManager


class TestContentManager:

    @pytest.fixture(scope='class')
    def content(self):
        class TestingHandler(BaseDocumentHandler):
            def process(self, document):
                return document

        directory = PurePath('/content')
        handlers = {'blog': TestingHandler}
        return ContentManager(directory, handlers)

    # Get handler.

    def test_get_handler(self, content):
        document = content.directory / 'blog/2019/article.adoc'
        handler = content.get_handler(document)
        assert handler.__class__ is content.handlers['blog']

    def test_get_handler_with_relative_path(self, content):
        document = PurePath('blog/article.adoc')
        handler = content.get_handler(document)
        assert handler.__class__ is content.handlers['blog']

    def test_get_missing_handler(self, content):
        document = content.directory / 'reviews/article.adoc'

        with pytest.raises(exceptions.HandlerNotFound):
            content.get_handler(document)

    def test_document_not_stored_in_content_directory(self, content):
        document = PurePath('/void/article.adoc')

        with pytest.raises(exceptions.InvalidDocumentLocation):
            content.get_handler(document)

    def test_document_not_categorized(self, content):
        document = content.directory / 'article.adoc'

        with pytest.raises(exceptions.DocumentNotCategorized):
            content.get_handler(document)


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

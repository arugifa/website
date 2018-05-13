from datetime import date
from pathlib import PurePath

import pytest

from website import update


class TestGetDocumentCallback:
    def test_get_callback(self):
        def expected():
            pass

        path = PurePath('blog/article.txt')
        callbacks = {'blog': expected, 'notes': lambda: 'test'}

        actual = update.get_document_callback(path, callbacks)
        assert actual is expected

    def test_unexisting_callback_raises_exception(self):
        path = PurePath('notes/note.txt')
        callbacks = {'blog': lambda: 'test'}

        with pytest.raises(KeyError):
            update.get_document_callback(path, callbacks)


class TestGetDocumentDate:
    def test_get_date(self):
        path = PurePath('blog/2018/04-08.article.adoc')
        actual = update.get_document_date(path)
        assert actual == date(2018, 4, 8)

    def test_document_must_be_classified_in_a_directory(self):
        path = PurePath('04-08.article.adoc')
        with pytest.raises(ValueError):
            update.get_document_date(path)

    def test_document_directory_must_contain_year_number(self):
        path = PurePath('blog/test/04-08.article.adoc')
        with pytest.raises(ValueError):
            update.get_document_date(path)

    def test_document_name_must_contain_month_and_day_numbers(self):
        path = PurePath('blog/test/article.adoc')
        with pytest.raises(ValueError):
            update.get_document_date(path)

        path = PurePath('blog/test/04.article.adoc')
        with pytest.raises(ValueError):
            update.get_document_date(path)

        path = PurePath('blog/test/04-.article.adoc')
        with pytest.raises(ValueError):
            update.get_document_date(path)

        path = PurePath('blog/test/john-doe.article.adoc')
        with pytest.raises(ValueError):
            update.get_document_date(path)


class TestGetDocumentType:
    def get_type(self):
        path = PurePath('notes/note.adoc')
        actual = update.get_document_type(path)
        assert actual == 'notes'

    def test_get_type_from_path_with_date(self):
        path = PurePath('/blog/2018/04-08.article.adoc')
        actual = update.get_document_type(path)
        assert actual == 'blog'

    def test_document_must_be_classified_in_a_directory(self):
        path = PurePath('04-08.article.adoc')
        with pytest.raises(ValueError):
            update.get_document_type(path)


class TestGetDocumentURI:
    def test_get_uri(self):
        path = PurePath('article.adoc')
        actual = update.get_document_uri(path)
        assert actual == 'article'

    def test_get_uri_from_path_with_date(self):
        path = PurePath('04-08.article.adoc')
        actual = update.get_document_uri(path)
        assert actual == 'article'

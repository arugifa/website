from datetime import date
from pathlib import PurePath

from website.utils import documents as utils


def test_retrieve_document_date():
    path = PurePath('blog/2018/04-08.article.adoc')
    actual = utils.retrieve_document_date(path)
    assert actual == date(2018, 4, 8)


def test_retrieve_document_type():
    path = PurePath('blog/2018/04-08.article.adoc')
    actual = utils.retrieve_document_type(path)
    assert actual == 'blog'


def test_retrieve_document_uri():
    path = PurePath('blog/2018/04-08.article.adoc')
    actual = utils.retrieve_document_uri(path)
    assert actual == 'article'

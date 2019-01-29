from pathlib import Path

import pytest

from website import exceptions
from website.blog.content import ArticleHandler
from website.blog.factories import ArticleFactory
from website.blog.models import Article

from tests._test_content import BaseDocumentHandlerTest


class TestArticleHandler(BaseDocumentHandlerTest):
    handler = ArticleHandler

    def test_insert_document(self):
        pass

    def test_update_document(self):
        pass

    def test_rename_document(self):
        pass

    # Delete article.

    def test_delete_document(self, db):
        article = ArticleFactory(uri='deletion')
        assert Article.all() == [article]

        path = Path('blog/2019/01-30.deletion.txt')
        self.handler(path).delete()
        assert Article.all() == []

    def test_delete_not_existing_document(self, db):
        path = Path('blog/2019/01-30.doesnt_exist.txt')
        with pytest.raises(exceptions.DocumentNotFound):
            self.handler(path).delete()

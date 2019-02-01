from datetime import date
from pathlib import Path

import pytest

from website import exceptions
from website.blog.content import ArticleHandler
from website.blog.factories import ArticleFactory, TagFactory
from website.blog.models import Article, Tag

from tests._test_content import BaseDocumentHandlerTest


class TestArticleHandler(BaseDocumentHandlerTest):
    handler = ArticleHandler

    # Insert article.

    def test_insert_document(self, db, fixtures, prompt):
        document = self.load_document(fixtures, prompt)
        document.rename('blog/2019/01-31.insert.html')
        article = self.handler(document, prompt=prompt).insert()

        assert article.uri == 'insert'
        self.assert_article_has_been_saved(article)

    def assert_article_has_been_saved(self, article):
        assert article.title == "House Music Spirit"
        assert article.introduction == "How House Music could save the world?"
        assert article.content == (
            '<h1>House Music Spirit</h1>'
            '<p id="preamble">How House Music could save the world?</p>'
            '<p>Just move your body.</p>'
            '<p>Feel the vibes...</p>'
            '<p>And never stop to dance!</p>'
        )

        assert article.category.uri == "music"
        assert article.category.name == "Music"

        assert len(article.tags) == 2
        assert article.tags[0].uri == "electro"
        assert article.tags[0].name == "Electro"
        assert article.tags[1].uri == "house"
        assert article.tags[1].name == "House"

    def load_document(self, fixtures, prompt):
        prompt.add_answers({
            r'name for the new "music" category': "Music",
            r'name for the new "house" tag': "House",
            r'name for the new "electro" tag': "Electro",
        })

        return fixtures['blog/article.html']

    def test_insert_already_existing_document(self, db, fixtures):
        ArticleFactory(uri='existing')

        document = fixtures['blog/article.html']
        document.rename('blog/2019/01-31.existing.html')

        with pytest.raises(exceptions.ItemAlreadyExisting):
            self.handler(document).insert()

    # Update article.

    def test_update_document(self, db, fixtures, prompt):
        original = ArticleFactory(
            uri='update', title="To Update",
            introduction="To be updated.", content="Please update me!",
        )
        assert original.last_update is None

        document = self.load_document(fixtures, prompt)
        document.rename('blog/2019/01-31.update.html')
        new = self.handler(document, prompt=prompt).update()

        assert new is original
        assert new.uri == 'update'
        assert new.last_update == date.today()
        self.assert_article_has_been_saved(new)

    def test_update_not_existing_document(self, db, fixtures):
        document = fixtures['blog/article.html']
        document.rename('blog/2019/01-31.missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            self.handler(document).update()

    # Rename document.

    def test_rename_document(self, db, fixtures, prompt):
        original = ArticleFactory(
            uri='rename', title="To Rename",
            introduction="To be renamed.", content="Please rename me!",
        )
        assert original.last_update is None

        document = self.load_document(fixtures, prompt)
        document.rename('blog/2019/01-31.rename.html')

        new_path = document.copy('blog/2019/01-31.new_name.html')
        new = self.handler(document, prompt=prompt).rename(new_path)

        assert new is original
        assert new.uri == 'new_name'
        assert new.last_update == date.today()
        self.assert_article_has_been_saved(new)

    def test_rename_not_existing_document(self, db, fixtures):
        document = fixtures['blog/article.html']
        document.rename('blog/2019/01-31.missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            self.handler(document).rename('new_name')

    # Delete article.

    def test_delete_document(self, db):
        article = ArticleFactory(uri='delete')
        assert Article.all() == [article]

        document = Path('blog/2019/01-30.delete.txt')
        self.handler(document).delete()
        assert Article.all() == []

    def test_delete_not_existing_document(self, db):
        document = Path('blog/2019/01-30.missing.txt')
        with pytest.raises(exceptions.ItemNotFound):
            self.handler(document).delete()

    def test_orphan_tags_are_also_deleted(self, db):
        tags = TagFactory.create_batch(2)
        ArticleFactory(tags=tags, uri='orphan_tags')
        assert Tag.all() == tags

        document = Path('blog/2019/01-30.orphan_tags.txt')
        self.handler(document).delete()
        assert Tag.all() == []

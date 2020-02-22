from datetime import date
from pathlib import PurePath

import pytest

from website.blog.factories import ArticleFactory
from website.blog.handlers import ArticleFileHandler
from website.blog.models import Article
from website.factories import CategoryFactory, TagFactory

from tests.base._test_handlers import BaseDocumentFileHandlerTest  # noqa: I100


class TestArticleFileHandler(BaseDocumentFileHandlerTest):
    handler = ArticleFileHandler
    factory = ArticleFactory

    @pytest.fixture
    def source_file(self, fixtures):
        return fixtures['blog/article.html']

    def assert_article_has_been_saved(self, article):
        assert article.title == "House Music Spirit"
        assert article.lead == "How House Music could save the world?"
        assert article.body == (
            '<div class="sect1">\n'
            '<h2 id="_tutorial">Tutorial</h2>\n'
            '<div class="sectionbody">\n'
            '<div class="paragraph">\n'
            '<p>Just move your body.</p>\n'
            '</div>\n</div>\n</div>\n'
            '<div class="sect1">\n'
            '<h2 id="_thats_it">That’s it?</h2>\n'
            '<div class="sectionbody">\n'
            '<div class="paragraph">\n'
            '<p>Feel the vibes…\u200b\nAnd never stop to dance!</p>\n'
            '</div>\n</div>\n</div>\n'
        )

        assert article.category.uri == "music"

        assert len(article.tags) == 3
        assert article.tags[0].uri == "electro"
        assert article.tags[1].uri == "funk"
        assert article.tags[2].uri == "house"

        assert article.publication_date == date(2019, 1, 31)

    async def test_insert_document(self, db, source_file):
        # Fixtures
        source_file.move('blog/2019/01-31.insert.html')

        CategoryFactory(uri='music')
        [TagFactory(uri=uri) for uri in ['house', 'electro', 'funk']]

        # Test
        article = await self.handler(source_file).insert()

        # Assertions
        assert article.exists()
        assert article.uri == 'insert'
        assert article.last_update is None
        self.assert_article_has_been_saved(article)

    async def test_update_document(self, db, source_file):
        # Fixtures
        original = ArticleFactory(
            uri='update', title="To Update",
            lead="To be updated.", body="Please update me!",
        )
        assert original.last_update is None

        source_file.move('blog/2019/01-31.update.html')

        CategoryFactory(uri='music')
        [TagFactory(uri=uri) for uri in ['house', 'electro', 'funk']]

        # Test
        updated = await self.handler(source_file).update()

        # Assertions
        assert updated is original
        assert updated.uri == 'update'
        assert updated.last_update == date.today()
        self.assert_article_has_been_saved(updated)

    async def test_rename_document(self, db, source_file):
        # Fixtures
        original = ArticleFactory(
            uri='rename', title="To Rename",
            lead="To be renamed.", body="Please rename me!",
        )
        assert original.last_update is None

        source_file.move('blog/2019/01-31.rename.html')
        new_path = source_file.symlink('blog/2019/01-31.new_name.html')

        CategoryFactory(uri='music')
        [TagFactory(uri=uri) for uri in ['house', 'electro', 'funk']]

        # Test
        handler = self.handler(source_file)
        renamed = await handler.rename(new_path)

        # Assertions
        assert renamed is original
        assert renamed.uri == 'new_name'
        assert renamed.last_update == date.today()
        self.assert_article_has_been_saved(renamed)

    def test_delete_document(self, db):
        article = ArticleFactory(uri='delete')
        source_file = PurePath('blog/2019/01-31.delete.html')

        assert Article.all() == [article]

        self.handler(source_file).delete()
        assert Article.all() == []
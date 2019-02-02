from datetime import date
from pathlib import Path, PurePath

import pytest

from website import exceptions
from website.blog.content import ArticleHandler, ArticleSourceParser
from website.blog.factories import ArticleFactory, TagFactory
from website.blog.models import Article, Tag

from tests._test_content import BaseDocumentHandlerTest, BaseDocumentSourceParserTest


class TestArticleHandler(BaseDocumentHandlerTest):
    handler = ArticleHandler

    @pytest.fixture
    def document(self, fixtures):
        return fixtures['blog/article.html']

    @pytest.fixture
    def answers(self, prompt):
        prompt.add_answers({
            r'name for the new "music" category': "Music",
            r'name for the new "house" tag': "House",
            r'name for the new "electro" tag': "Electro",
        })

    # Insert article.

    def test_insert_document(self, answers, db, document, prompt):
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

    def test_insert_already_existing_document(self, db, document):
        ArticleFactory(uri='existing')
        document.rename('blog/2019/01-31.existing.html')

        with pytest.raises(exceptions.ItemAlreadyExisting):
            self.handler(document).insert()

    # Update article.

    def test_update_document(self, answers, db, document, prompt):
        original = ArticleFactory(
            uri='update', title="To Update",
            introduction="To be updated.", content="Please update me!",
        )
        assert original.last_update is None

        document.rename('blog/2019/01-31.update.html')
        new = self.handler(document, prompt=prompt).update()

        assert new is original
        assert new.uri == 'update'
        assert new.last_update == date.today()
        self.assert_article_has_been_saved(new)

    def test_update_not_existing_document(self, db, document):
        document.rename('blog/2019/01-31.missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            self.handler(document).update()

    # Rename document.

    def test_rename_document(self, answers, db, document, prompt):
        original = ArticleFactory(
            uri='rename', title="To Rename",
            introduction="To be renamed.", content="Please rename me!",
        )
        assert original.last_update is None

        document.rename('blog/2019/01-31.rename.html')
        new_path = document.copy('blog/2019/01-31.new_name.html')
        new = self.handler(document, prompt=prompt).rename(new_path)

        assert new is original
        assert new.uri == 'new_name'
        assert new.last_update == date.today()
        self.assert_article_has_been_saved(new)

    def test_rename_not_existing_document(self, db, document):
        document.rename('blog/2019/01-31.missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            self.handler(document).rename('new_name')

    # Delete article.

    def test_delete_document(self, db):
        article = ArticleFactory(uri='delete')
        assert Article.all() == [article]

        document = PurePath('blog/2019/01-30.delete.html')
        self.handler(document).delete()
        assert Article.all() == []

    def test_delete_not_existing_document(self, db):
        document = PurePath('blog/2019/01-30.missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            self.handler(document).delete()

    def test_orphan_tags_are_also_deleted(self, db):
        tags = TagFactory.create_batch(2)
        ArticleFactory(tags=tags, uri='orphan_tags')
        assert Tag.all() == tags

        document = PurePath('blog/2019/01-30.orphan_tags.html')
        self.handler(document).delete()
        assert Tag.all() == []

    # Parse date.

    def test_scan_date(self):
        path = PurePath('blog/2018/08-04.date.html')
        actual = self.handler(path).scan_date()
        assert actual == date(2018, 8, 4)

    def test_articles_must_be_organized_by_year(self):
        path = PurePath('blog/04-08.article.txt')
        with pytest.raises(ValueError):
            self.handler(path).scan_date()

    @pytest.mark.parametrize('path', [
        'blog/2019/article.txt',
        'blog/2019/04.article.txt',
        'blog/2019/04-.article.txt',
        'blog/2019/john-doe.article.txt',
    ])
    def test_articles_must_be_classified_by_month_and_day(self, path):
        path = PurePath(path)
        with pytest.raises(ValueError):
            self.handler(path).scan_date()


class TestArticleSourceParser(BaseDocumentSourceParserTest):
    parser = ArticleSourceParser

    @pytest.fixture(scope='class')
    def source(self, fixtures):
        article = fixtures['blog/article.html'].open().read()
        return self.parser(article)

    @pytest.fixture(scope='class')
    def empty_source(self):
        return self.parser('<html></html>')

    # Find category.

    def test_parse_category(self, source):
        category = source.parse_category()
        assert category == 'music'

    def test_parse_not_defined_category(self, empty_source):
        with pytest.raises(exceptions.CategoryNotDefined):
            empty_source.parse_category()

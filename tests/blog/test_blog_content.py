from datetime import date
from pathlib import PurePath

import pytest

from website import exceptions
from website.blog.content import ArticleHandler, ArticleSourceParser
from website.blog.factories import ArticleFactory, CategoryFactory, TagFactory
from website.blog.models import Article

from tests._test_content import (  # noqa: I100
    BaseDocumentHandlerTest, BaseDocumentSourceParserTest)


class TestArticleHandler(BaseDocumentHandlerTest):
    handler = ArticleHandler
    factory = ArticleFactory

    @pytest.fixture
    def source_file(self, fixtures):
        return fixtures['blog/article.html']

    @pytest.fixture
    def answers(self, prompt):
        prompt.add_answers({
            r'name for the new "music" category': "Music",
            r'name for the new "house" tag': "House",
            r'name for the new "electro" tag': "Electro",
            r'name for the new "funk" tag': "Funk",
        })

    # Insert article.

    async def test_insert_document(self, answers, db, prompt, source_file):
        source_file.move('blog/2019/01-31.insert.html')
        article = await self.handler(source_file, prompt=prompt).insert()

        assert article.exists()
        assert article.uri == 'insert'
        assert article.last_update is None
        self.assert_article_has_been_saved(article)

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
        assert article.category.name == "Music"

        assert len(article.tags) == 3
        assert article.tags[0].uri == "electro"
        assert article.tags[0].name == "Electro"
        assert article.tags[1].uri == "funk"
        assert article.tags[1].name == "Funk"
        assert article.tags[2].uri == "house"
        assert article.tags[2].name == "House"

        assert article.publication_date == date.today()

    async def test_insert_already_existing_document(self, db, source_file):
        ArticleFactory(uri='existing')
        source_file.move('blog/2019/01-31.existing.html')

        with pytest.raises(exceptions.ItemAlreadyExisting):
            await self.handler(source_file).insert()

    async def test_insert_documents_in_batch(self, answers, db, prompt, source_file):
        # Test
        source_file_1 = source_file.symlink('blog/2019/03-08.batch_1.html')
        handler_1 = self.handler(source_file_1, prompt=prompt)
        article_1 = await handler_1.insert(batch=True)

        source_file_2 = source_file.symlink('blog/2019/03-08.batch_2.html')
        handler_2 = self.handler(source_file_2, prompt=prompt)
        article_2 = await handler_2.insert(batch=True)

        assert not article_1.exists()
        assert not article_2.exists()

        prompt.answer_quiz()
        article_1.save()
        article_2.save()

        # Assertions
        assert article_1.exists()
        assert article_1.uri == 'batch_1'
        assert article_1.last_update is None
        self.assert_article_has_been_saved(article_1)

        assert article_2.exists()
        assert article_2.uri == 'batch_2'
        assert article_2.last_update is None
        self.assert_article_has_been_saved(article_2)

    # Update article.

    async def test_update_document(self, answers, db, prompt, source_file):
        original = ArticleFactory(
            uri='update', title="To Update",
            lead="To be updated.", body="Please update me!",
        )
        assert original.last_update is None

        source_file.move('blog/2019/01-31.update.html')
        updated = await self.handler(source_file, prompt=prompt).update()

        assert updated is original
        assert updated.uri == 'update'
        assert updated.last_update == date.today()
        self.assert_article_has_been_saved(updated)

    async def test_update_not_existing_document(self, db, source_file):
        source_file.move('blog/2019/01-31.missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            await self.handler(source_file).update()

    async def test_update_documents_in_batch(self, answers, db, prompt, source_file):
        # Fixtures
        source_file_1 = source_file.symlink('blog/2019/03-08.batch_1.html')
        original_1 = ArticleFactory(
            uri='batch_1', title="To Update",
            lead="To be updated.", body="Please update me!",
        )
        assert original_1.last_update is None

        source_file_2 = source_file.symlink('blog/2019/03-08.batch_2.html')
        original_2 = ArticleFactory(
            uri='batch_2', title="To Update",
            lead="To be updated.", body="Please update me!",
        )
        assert original_2.last_update is None

        # Test
        handler_1 = self.handler(source_file_1, prompt=prompt)
        updated_1 = await handler_1.update(batch=True)

        assert updated_1 is original_1
        assert updated_1.last_update is None

        handler_2 = self.handler(source_file_2, prompt=prompt)
        updated_2 = await handler_2.update(batch=True)

        assert updated_2 is original_2
        assert updated_2.last_update is None

        prompt.answer_quiz()
        updated_1.save()
        updated_2.save()

        # Assertions
        assert updated_1 is original_1
        assert updated_1.uri == 'batch_1'
        assert updated_1.last_update == date.today()
        self.assert_article_has_been_saved(updated_1)

        assert updated_2 is original_2
        assert updated_2.uri == 'batch_2'
        assert updated_2.last_update == date.today()
        self.assert_article_has_been_saved(updated_2)

    # Rename article.

    async def test_rename_document(self, answers, db, prompt, source_file):
        original = ArticleFactory(
            uri='rename', title="To Rename",
            lead="To be renamed.", body="Please rename me!",
        )
        assert original.last_update is None

        source_file.move('blog/2019/01-31.rename.html')
        new_path = source_file.symlink('blog/2019/01-31.new_name.html')
        handler = self.handler(source_file, prompt=prompt)
        renamed = await handler.rename(new_path)

        assert renamed is original
        assert renamed.uri == 'new_name'
        assert renamed.last_update == date.today()
        self.assert_article_has_been_saved(renamed)

    async def test_rename_not_existing_document(self, db, source_file):
        source_file.move('blog/2019/01-31.missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            await self.handler(source_file).rename('new_name')

    async def test_rename_documents_in_batch(self, answers, db, prompt, source_file):
        # Fixtures
        source_file_1 = source_file.symlink('blog/2019/03-08.batch_1.html')
        original_1 = ArticleFactory(
            uri='batch_1', title="To Rename",
            lead="To be renamed.", body="Please rename me!",
        )
        assert original_1.last_update is None

        source_file_2 = source_file.symlink('blog/2019/03-08.batch_2.html')
        original_2 = ArticleFactory(
            uri='batch_2', title="To Rename",
            lead="To be renamed.", body="Please rename me!",
        )
        assert original_2.last_update is None

        # Test
        new_path_1 = source_file.symlink('blog/2019/03-08.new_name_1.html')
        handler_1 = self.handler(source_file_1, prompt=prompt)
        renamed_1 = await handler_1.rename(new_path_1, batch=True)

        assert renamed_1 is original_1
        assert renamed_1.uri == 'new_name_1'
        assert renamed_1.last_update is None

        new_path_2 = source_file.symlink('blog/2019/03-08.new_name_2.html')
        handler_2 = self.handler(source_file_2, prompt=prompt)
        renamed_2 = await handler_2.rename(new_path_2, batch=True)

        assert renamed_2 is original_2
        assert renamed_2.uri == 'new_name_2'
        assert renamed_2.last_update is None

        prompt.answer_quiz()
        renamed_1.save()
        renamed_2.save()

        # Assertions
        assert renamed_1 is original_1
        assert renamed_1.uri == 'new_name_1'
        assert renamed_1.last_update == date.today()
        self.assert_article_has_been_saved(renamed_1)

        assert renamed_2 is original_2
        assert renamed_2.uri == 'new_name_2'
        assert renamed_2.last_update == date.today()
        self.assert_article_has_been_saved(renamed_2)

    # Delete article.

    def test_delete_document(self, db):
        article = ArticleFactory(uri='delete')
        source_file = PurePath('blog/2019/01-30.delete.html')

        assert Article.all() == [article]

        self.handler(source_file).delete()
        assert Article.all() == []

    def test_delete_not_existing_document(self, db):
        source_file = PurePath('blog/2019/01-30.missing.html')

        with pytest.raises(exceptions.ItemNotFound):
            self.handler(source_file).delete()

    # Insert category.

    async def test_insert_new_category(self, answers, db, prompt, source_file):
        source_file.move('blog/2019/03-06.insert_category.html')
        article = ArticleFactory(uri='insert_category')

        await self.handler(source_file, prompt=prompt).insert_category()

        assert article.category.uri == 'music'
        assert article.category.name == 'Music'

    async def test_insert_existing_category(self, db, source_file):
        source_file.move('blog/2019/03-06.insert_category.html')
        article = ArticleFactory(uri='insert_category')

        category = CategoryFactory(uri='music', name='Musika')
        await self.handler(source_file).insert_category()

        # Let's be sure that attributes have not changed.
        assert article.category is category
        assert category.uri == 'music'
        assert category.name == 'Musika'

    async def test_insert_category_later(self, answers, db, prompt, source_file):
        source_file.move('blog/2019/03-07.insert_category.html')
        category = CategoryFactory()
        article = ArticleFactory(uri='insert_category', category=category)

        handler = self.handler(source_file, prompt=prompt)
        await handler.insert_category(later=True)

        assert article.category is category
        prompt.answer_quiz()
        assert article.category is not category

        assert article.category.uri == 'music'
        assert article.category.name == 'Music'

    # Insert tags.

    async def test_insert_new_tags(self, answers, db, prompt, source_file):
        source_file.move('blog/2019/03-06.insert_tags.html')
        article = ArticleFactory(uri='insert_tags')

        await self.handler(source_file, prompt=prompt).insert_tags()

        assert len(article.tags) == 3
        assert article.tags[0].uri == 'electro'
        assert article.tags[0].name == 'Electro'
        assert article.tags[1].uri == 'funk'
        assert article.tags[1].name == 'Funk'
        assert article.tags[2].uri == 'house'
        assert article.tags[2].name == 'House'

    async def test_insert_existing_tags(self, db, source_file):
        source_file.move('blog/2019/03-06.insert_tags.html')
        article = ArticleFactory(uri='insert_tags')

        expected = [
            TagFactory(uri='electro', name='Electrico'),
            TagFactory(uri='funk', name='Funky'),
            TagFactory(uri='house', name='Maison'),
        ]
        await self.handler(source_file).insert_tags()

        # Let's be sure that attributes have not changed.
        assert len(article.tags) == len(expected)
        assert article.tags[0].uri == 'electro'
        assert article.tags[0].name == 'Electrico'
        assert article.tags[1].uri == 'funk'
        assert article.tags[1].name == 'Funky'
        assert article.tags[2].uri == 'house'
        assert article.tags[2].name == 'Maison'

    async def test_insert_tags_that_do_not_all_exist(
            self, answers, db, prompt, source_file):
        source_file.move('blog/2019/03-06.insert_tags.html')
        article = ArticleFactory(uri='insert_tags')

        existing = TagFactory(uri='funk', name='Funky')
        handler = self.handler(source_file, prompt=prompt)
        await handler.insert_tags()

        assert len(article.tags) == 3
        assert article.tags[0].uri == 'electro'
        assert article.tags[0].name == 'Electro'
        assert article.tags[2].uri == 'house'
        assert article.tags[2].name == 'House'

        # Let's be sure that attributes of the existing tag have not changed.
        assert article.tags[1] is existing
        assert article.tags[1].uri == 'funk'
        assert article.tags[1].name == 'Funky'

    async def test_insert_tags_later(self, answers, db, prompt, source_file):
        source_file.move('blog/2019/03-07.insert_tags.html')
        article = ArticleFactory(uri='insert_tags', tags=[])

        await self.handler(source_file, prompt=prompt).insert_tags(later=True)

        assert len(article.tags) == 0
        prompt.answer_quiz()
        assert len(article.tags) == 3

        assert article.tags[0].uri == 'electro'
        assert article.tags[0].name == 'Electro'
        assert article.tags[1].uri == 'funk'
        assert article.tags[1].name == 'Funk'
        assert article.tags[2].uri == 'house'
        assert article.tags[2].name == 'House'

    # Scan date.

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
        source_file = fixtures['blog/article.html'].open().read()
        return self.parser(source_file)

    # Parse category.

    def test_parse_category(self, source):
        category = source.parse_category()
        assert category == 'music'

    @pytest.mark.parametrize('html', [
        '<html><head></head></html>',
        '<html><head><meta name="description"></head></html>',
    ])
    def test_parse_missing_category(self, html):
        with pytest.raises(exceptions.ArticleCategoryMissing):
            self.parser(html).parse_category()

    # Parse lead.

    def test_parse_lead(self, source):
        lead = source.parse_lead()
        assert lead == "How House Music could save the world?"

    @pytest.mark.parametrize('content', [
        '<div id="preamble"></div>',
        '<div id="preamble"><p></p></div>',
    ])
    def test_parse_missing_lead(self, content):
        html = f'<html><body><div id="content">{content}</div></body></html>'
        with pytest.raises(exceptions.ArticleLeadMissing):
            self.parser(html).parse_lead()

    def test_parse_lead_with_many_paragraphs(self):
        html = (
            '<html><body><div id="content"><div id="preamble">'
            '<p>Paragraph 1</p>'
            '<p>Paragraph 2</p>'
            '</div></div></body></html>'
        )
        with pytest.raises(exceptions.ArticleLeadMalformatted):
            self.parser(html).parse_lead()

    def test_parse_lead_with_new_lines(self):
        html = (
            '<html><body><div id="content">'
            '<div id="preamble"><p>Not enough\nspace?</p></div>'
            '</div></body></html>'
        )
        lead = self.parser(html).parse_lead()
        assert lead == "Not enough space?"

    def test_parse_lead_surrounded_by_new_lines_and_tabulations(self):
        html = (
            '<html><body><div id="content">'
            '<div id="preamble">\n\t<p>\n\t\tLead\n\t\t</p>\n\t</div>'
            '</div></body></html>'
        )
        lead = self.parser(html).parse_lead()
        assert lead == "Lead"

    # Parse body.

    def test_parse_body(self, source):
        actual = source.parse_body()
        expected = (
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
        assert actual == expected

    def test_parse_missing_body(self):
        html = f'<html><body><div id="content"></div></body></html>'
        with pytest.raises(exceptions.ArticleBodyMissing):
            self.parser(html).parse_body()

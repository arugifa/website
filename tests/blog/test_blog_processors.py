from datetime import date
from pathlib import PurePath

import pytest

from website.blog import exceptions
from website.blog.processors import ArticleFileProcessor
from website.factories import CategoryFactory, TagFactory

from tests.base._test_processors import BaseDocumentFileProcessorTest  # noqa: I100


class TestArticleFileProcessor(BaseDocumentFileProcessorTest):
    processor = ArticleFileProcessor

    @pytest.fixture
    def source_file(self, fixtures):
        return fixtures['blog/article.html']

    # Process file.

    async def test_process_file(self, app, db, source_file):
        source_file.rename('blog/2020/02-15.analyze.html')
        processor = self.processor(source_file)

        category = CategoryFactory(uri='music')
        tags = [TagFactory(uri=uri) for uri in ['electro', 'funk', 'house']]

        actual, errors = await processor.process()
        expected = {
            'title': "House Music Spirit",
            'category': category,
            'lead': "How House Music could save the world?",
            'body': (
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
            ),
            'tags': tags,
            'publication_date': date(2020, 2, 15),
        }

        assert actual == expected
        assert errors == set()

    # Scan date.

    def test_scan_date(self):
        path = PurePath('blog/2018/08-04.date.html')
        actual = self.processor(path).scan_date()
        assert actual == date(2018, 8, 4)

    def test_articles_must_be_organized_by_year(self):
        path = PurePath('blog/04-08.article.txt')

        with pytest.raises(exceptions.ArticleInvalidLocation):
            self.processor(path).scan_date()

    @pytest.mark.parametrize('path', [
        'blog/2019/article.txt',
        'blog/2019/04.article.txt',
        'blog/2019/04-.article.txt',
        'blog/2019/john-doe.article.txt',
    ])
    def test_articles_must_be_classified_by_month_and_day(self, path):
        path = PurePath(path)

        with pytest.raises(exceptions.ArticleDateMalformatted):
            self.processor(path).scan_date()

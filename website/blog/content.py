"""Manage content updates of my blog."""

import re
from datetime import date
from typing import List

import lxml.etree
from lxml.cssselect import CSSSelector

from website import exceptions
from website.blog.models import Article, Category, Tag
from website.content import BaseDocumentHandler, BaseDocumentSourceParser


class ArticleSourceParser(BaseDocumentSourceParser):
    """Parse source file of a blog article."""

    def parse_category(self) -> str:
        """Look for article's category.

        :raise ~.ArticleCategoryMissing: when no category is found.
        """
        parser = CSSSelector('html head meta[name=description]')

        try:
            category = parser(self.source)[0].get('content')
            assert category is not None
        except (AssertionError, IndexError):
            raise exceptions.ArticleCategoryMissing(self)

        return category

    def parse_lead(self) -> str:
        """Look for article's lead paragraph.

        :raise ~.ArticleLeadMissing:
            when no lead paragraph is found.
        :raise ~.ArticleLeadMalformatted:
            when multiple lead paragraphs are found.
        """
        parser = CSSSelector('html body div#content div#preamble p')
        lead = parser(self.source)

        try:
            assert len(lead) < 2
        except AssertionError:
            raise exceptions.ArticleLeadMalformatted(self)

        try:
            lead = lead[0].text_content().strip()
            lead = re.sub(r'\s+', r' ', lead)
            assert lead
        except (AssertionError, IndexError):
            raise exceptions.ArticleLeadMissing(self)

        return lead

    def parse_body(self) -> str:
        """Look for article's body.

        :raise ~.ArticleBodyMissing: when no body is found.
        """
        parser = CSSSelector('html body div#content div.sect1')
        body = parser(self.source)

        try:
            assert body
        except AssertionError:
            raise exceptions.ArticleBodyMissing(self)

        body = ''.join(lxml.etree.tounicode(section) for section in body)

        return body


class ArticleHandler(BaseDocumentHandler):
    """Manage the life cycle of a blog article in database.

    Inside its repository, the article's source file must be organized by year,
    and then classified by month and day, as follows:
    ``blog/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>``
    """

    model = Article
    parser = ArticleSourceParser

    # Main API

    def delete(self) -> None:
        """Delete article from database, and clean orphan tags.

        :raise ~.ItemNotFound: if the article doesn't exist.
        """
        super().delete()  # Can raise ItemNotFound
        Tag.delete_orphans()

    # Helpers

    def process(self, article: Article) -> None:
        """Parse :attr:`path` and update an article already loaded from database.

        If the article has new category/tags which don't exist yet in database,
        then these latter are created interactively (i.e., by asking questions
        to the user if necessary).

        :param article: the article to update.
        """  # noqa: E501
        source = self.load()

        article.title = source.parse_title()
        article.lead = source.parse_lead()
        article.body = source.parse_body()
        article.category = self.insert_category(source)
        article.tags = self.insert_tags(source)

    def insert_category(self, source: ArticleSourceParser = None) -> Category:
        """Return article's category, and create it in database if necessary.

        If already loaded previously, the article's source file can be given as
        an argument, to not load it again, and avoid inconsistencies if the
        file changed in the meantime.
        """
        source = source or self.load()
        uri = source.parse_category()

        try:
            category = Category.find(uri=uri)
        except exceptions.ItemNotFound:
            name = self.prompt(
                f'Please enter a name for the new "{uri}" category: ')
            category = Category(uri=uri, name=name)
            category.save()

        return category

    def insert_tags(self, source: ArticleSourceParser = None) -> List[Tag]:
        """Return article's tags, and create new ones in database if necessary.

        If already loaded previously, the article's source file can be given as
        an argument, to not load it again, and avoid inconsistencies if the
        file changed in the meantime.
        """
        source = source or self.load()
        uris = source.parse_tags()
        tags = Tag.filter(uri=uris)

        existing = set([tag.uri for tag in tags])
        new = set(uris) - existing

        for uri in new:
            name = self.prompt(
                f'Please enter a name for the new "{uri}" tag: ')
            tag = Tag(uri=uri, name=name)
            tag.save()
            tags.append(tag)

        return sorted(tags, key=lambda t: t.uri)

    # Path Scanners

    def scan_date(self) -> date:
        """Return article's creation date, based on its :attr:`path`.

        :raise ~.ArticleDateMalformatted: when the article is not
        """
        try:
            year = int(self.path.parent.name)
            month, day = map(int, self.path.name.split('.')[0].split('-'))
        except (IndexError, TypeError):
            raise exceptions.ArticleDateMalformatted(self)

        return date(year, month, day)

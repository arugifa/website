"""Content management of my blog."""

import logging
import re
from datetime import date
from typing import Iterable, List

import lxml.etree
from lxml.cssselect import CSSSelector

from website import exceptions
from website.blog.models import Article, Category, Tag
from website.content import BaseDocumentHandler, BaseDocumentSourceParser

logger = logging.getLogger(__name__)


class ArticleSourceParser(BaseDocumentSourceParser):
    """...

    See https://asciidoctor.org/docs/user-manual/
    """

    def parse_category(self) -> str:
        """Search the category of an article in its HTML source.

        :raise website.exceptions.ArticleCategoryMissing:
            when no category is found.
        """
        parser = CSSSelector('html head meta[name=description]')

        try:
            category = parser(self.source)[0].get('content')
            assert category is not None
        except (AssertionError, IndexError):
            raise exceptions.ArticleCategoryMissing

        return category

    def parse_title(self) -> str:
        """Search the title of an article, inside its HTML source.

        :raise website.exceptions.ArticleTitleMissing: when no title is found.
        """
        parser = CSSSelector('html head title')

        try:
            title = parser(self.source)[0].text_content()
            assert title
        except (AssertionError, IndexError):
            raise exceptions.ArticleTitleMissing

        return title

    def parse_lead(self) -> str:
        """Search the lead of an article, inside its HTML source.

        :raise website.exceptions.ArticleLeadMissing:
            when no lead is found.
        :raise website.exceptions.ArticleLeadMalformatted:
            when the lead contains many paragraphs.
        """
        parser = CSSSelector('html body div#content div#preamble p')
        lead = parser(self.source)

        try:
            assert len(lead) < 2
        except AssertionError:
            raise exceptions.ArticleLeadMalformatted

        try:
            lead = lead[0].text_content().strip()
            lead = re.sub(r'\s+', r' ', lead)
            assert lead
        except (AssertionError, IndexError):
            raise exceptions.ArticleLeadMissing

        return lead

    def parse_body(self) -> str:
        """Search the content of an article, inside its HTML source.

        :raise website.exceptions.ArticleBodyMissing:
            when no body is found.
        """
        parser = CSSSelector('html body div#content div.sect1')
        body = parser(self.source)

        try:
            assert body
        except AssertionError:
            raise exceptions.ArticleBodyMissing

        body = ''.join(lxml.etree.tounicode(section) for section in body)

        return body


class ArticleHandler(BaseDocumentHandler):
    """Manage articles life cycle."""
    model = Article
    parser = ArticleSourceParser

    # Main API

    def delete(self) -> None:
        """Delete an article from database, and clean orphan tags.

        :raise website.exceptions.ItemNotFound:
            if the article doesn't exist.
        """
        super().delete()  # Can raise ItemNotFound
        Tag.delete_orphans()

    # Helpers

    def process(self, article: Article) -> Article:
        """Update an article in database.

        :param create:
            create the article if it doesn't exist yet in database.
        :raise website.exceptions.ItemNotFound:
            if the article cannot be found, and ``create`` is set to ``False``.
        """
        with self.load() as source:
            article.title = source.parse_title()
            article.lead = source.parse_lead()
            article.body = source.parse_body()

            category_uri = source.parse_category()
            tag_uris = source.parse_tags()

        article.category = self.insert_category(category_uri)
        article.tags = self.insert_tags(tag_uris)

        return article

    def insert_category(self, uri: str) -> Category:
        """Create the article's category, if it doesn't exist yet."""
        try:
            category = Category.find(uri=uri)
        except exceptions.ItemNotFound:
            name = self.prompt(f'Please enter a name for the new "{uri}" category: ')
            category = Category(uri=uri, name=name)
            category.save()

        return category

    def insert_tags(self, uris: Iterable[str]) -> List[Tag]:
        """Create the article's tags, if they don't exist yet."""
        tags = Tag.filter(uri=uris)

        existing = set([tag.uri for tag in tags])
        new = set(uris) - existing

        for uri in new:
            name = self.prompt(f'Please enter a name for the new "{uri}" tag: ')
            tag = Tag(name=name, uri=uri)
            tag.save()
            tags.append(tag)

        return sorted(tags, key=lambda t: t.uri)

    # Path Scanners

    def scan_date(self) -> date:
        """Return the creation date of a document, based on its :attr:`path`."""  # noqa: E501
        try:
            year = int(self.path.parent.name)
            month, day = map(int, self.path.name.split('.')[0].split('-'))
        except (IndexError, TypeError):
            error = 'Path "%s" does not contain a proper date'
            logger.error(error, self.path)
            raise ValueError(error % self.path)

        return date(year, month, day)

"""Content management of my blog."""

import logging
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup
from lxml.cssselect import CSSSelector
from lxml.html import HtmlElement

from website.blog.models import Article, Category, Tag
from website.content import BaseDocumentHandler, BaseDocumentSourceParser
from website.exceptions import CategoryNotDefined, ItemNotFound

logger = logging.getLogger(__name__)


class ArticleSourceParser(BaseDocumentSourceParser):
    def parse_category(self) -> str:
        """Search the category of an article in its HTML source.

        :raise website.exceptions.CategoryNotDefined:
            when no category is found.
        """
        parser = CSSSelector('html head meta[name=description]')

        try:
            category = parser(self.source)[0].get('content')
            assert category is not None
        except (AssertionError, IndexError):
            raise CategoryNotDefined

        return category

    # To implement
    def parse_content(self) -> Optional[str]:
        """Search the content of an article, inside its HTML source."""
        # TODO: Return only article's body, not the whole content (01/2019)
        html = BeautifulSoup(self._source, 'html.parser')

        try:
            return ''.join(str(child) for child in html.body.find_all())
        except AttributeError:
            return None

    def parse_introduction(self) -> Optional[str]:
        """Search the introduction of an article, inside its HTML source."""
        html = BeautifulSoup(self._source, 'html.parser')

        try:
            return html.body.select_one('#preamble').text.strip()
        except AttributeError:
            return None

    def parse_title(self) -> Optional[str]:
        """Search the title of an article, inside its HTML source."""
        html = BeautifulSoup(self._source, 'html.parser')

        try:
            return html.body.select_one('h1').text
        except AttributeError:
            return None


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
            article.introduction = source.parse_introduction()
            article.content = source.parse_content()

            category_uri = source.parse_category()
            tag_uris = source.parse_tags()

        article.category = self.insert_category(category_uri)
        article.tags = self.insert_tags(tag_uris)

        return article

    def insert_category(self, uri: str) -> Category:
        """Create the article's category, if it doesn't exist yet."""
        try:
            category = Category.find(uri=uri)
        except ItemNotFound:
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

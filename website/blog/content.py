"""Manage content updates of my blog."""

import logging
import re
from datetime import date
from functools import partial
from typing import Iterable

import lxml.etree
from lxml.cssselect import CSSSelector

from website import exceptions
from website.blog.models import Article, Category, Tag
from website.content import BaseDocumentHandler, BaseDocumentSourceParser

logger = logging.getLogger(__name__)


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

    async def process(self, *, batch: bool = False) -> None:
        """Parse :attr:`path` and update :attr:`document`'s attributes.

        :param batch:
            set to ``True`` to delay some actions requiring user input.
            Useful when several documents are processed in parallel.
        """
        source = await self.source

        self.document.title = source.parse_title()
        self.document.lead = source.parse_lead()
        self.document.body = source.parse_body()

        await self.insert_category(later=batch)
        await self.insert_tags(later=batch)

    # Helpers

    async def insert_category(self, *, later: bool = False) -> None:
        """Parse and save article's category.

        If not already existing, the category is then created in database.

        :param later: set to ``True`` to postpone user input.
        """
        source = await self.source
        uri = source.parse_category()

        insertion = partial(self._insert_category, uri)

        if later:
            self.prompt.solve_later(insertion)
        else:
            insertion()

    def _insert_category(self, uri: str) -> None:
        try:
            category = Category.find(uri=uri)
        except exceptions.ItemNotFound:
            name = self.prompt.ask_for(Category.name, uri=uri)

            category = Category(uri=uri, name=name)
            category.save()

            logger.info("Created new category: %s", category.uri)

        self.document.category = category

    async def insert_tags(self, *, later: bool = False) -> None:
        """Parse and save article's tags.

        If not already existing, missing tags are created in database.

        :param later: set to ``True`` to postpone user input.
        """
        source = await self.source
        tag_uris = set(source.parse_tags())

        insertion = partial(self._insert_tags, tag_uris)

        if later:
            self.prompt.solve_later(insertion)
        else:
            insertion()

    def _insert_tags(self, uris: Iterable[str]) -> None:
        existing_tags = Tag.filter(uri=uris)
        self.document.tags = existing_tags

        new_tags = uris - set(t.uri for t in existing_tags)

        for uri in new_tags:
            name = self.prompt.ask_for(Tag.name, uri=uri)

            tag = Tag(uri=uri, name=name)
            tag.save()
            self.document.tags.add(tag)

            logger.info("Created new tag: %s", tag.uri)

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

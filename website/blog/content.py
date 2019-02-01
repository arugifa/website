"""Content management of my blog."""

from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup

from website.blog.models import Article, Category, Tag
from website.content import BaseDocumentHandler
from website.exceptions import ItemNotFound


class ArticleHandler(BaseDocumentHandler):
    """Manage articles life cycle."""
    model = Article

    def delete(self) -> None:
        """Delete an article from database, and clean orphan tags.

        :raise website.exceptions.ItemNotFound:
            if the article doesn't exist.
        """
        super().delete()  # Can raise ItemNotFound
        Tag.delete_orphans()

    def process(self, article: Article) -> Article:
        """Update an article in database.

        :param create:
            create the article if it doesn't exist yet in database.
        :raise website.exceptions.ItemNotFound:
            if the article cannot be found, and ``create`` is set to ``False``.
        """
        source = self.read()
        html = BeautifulSoup(source, 'html.parser')

        article.title = self.parse_title(html)
        article.introduction = self.parse_introduction(html)
        article.content = self.get_content(html)

        category_uri = self.parse_category(html)
        article.category = self.insert_category(category_uri)

        tag_uris = self.parse_tags(html)
        article.tags = self.insert_tags(tag_uris)

        return article

    # Helpers

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

    @staticmethod
    def get_content(html: BeautifulSoup) -> Optional[str]:
        """Search the content of an article, inside its HTML source."""
        # TODO: Return only article's body, not the whole content (01/2019)
        try:
            return ''.join(str(child) for child in html.body.find_all())
        except AttributeError:
            return None

    @staticmethod
    def parse_category(html: BeautifulSoup) -> Optional[str]:
        """Search the category of an article, inside its HTML source."""
        try:
            return html.head.select_one('meta[name=description]')['content']
        except (KeyError, TypeError):
            return None

    @staticmethod
    def parse_introduction(html: BeautifulSoup) -> Optional[str]:
        """Search the introduction of an article, inside its HTML source."""
        try:
            return html.body.select_one('#preamble').text.strip()
        except AttributeError:
            return None

    @staticmethod
    def parse_tags(html: BeautifulSoup) -> List[str]:
        """Search the tags of an article, inside its HTML source."""
        try:
            tags = html.head.select_one('meta[name=keywords]')['content']
        except (KeyError, TypeError):
            return list()

        return tags.split(', ')

    @staticmethod
    def parse_title(html: BeautifulSoup) -> Optional[str]:
        """Search the title of an article, inside its HTML source."""
        try:
            return html.body.select_one('h1').text
        except AttributeError:
            return None

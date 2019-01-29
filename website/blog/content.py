"""Content management of my blog."""

from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup

from website.blog.models import Article, Category, Tag
from website.content import BaseDocumentHandler


class ArticleHandler(BaseDocumentHandler):
    """Manage articles life cycle."""

    def insert(self) -> Article:
        """Insert an article into database."""
        uri = self.parse_uri()
        date = self.parse_date()

        source = self.read()
        html = BeautifulSoup(source, 'html.parser')

        title = self.parse_title(html)
        introduction = self.parse_introduction(html)
        content = self.parse_content(html)

        category_uri = self.parse_category(html)
        category = self.insert_category(category_uri)

        tag_uris = self.parse_tags(html)
        tags = self.insert_tags(tag_uris)

        article = Article(
            uri=uri, title=title,
            introduction=introduction, content=content,
            category=category, tags=tags,
            publication_date=date,
        )
        article.save()

        return article

    def update(self) -> Article:
        """Update an article in database."""
        uri = self.parse_uri(self.path)
        article = Article.find(uri=uri)

        source = self.read(self.path)
        html = BeautifulSoup(source, 'html.parser')

        article.title = self.parse_title(html)
        article.introduction = self.parse_introduction(html)
        article.content = self.parse_content(html)

        category_uri = self.parse_category(html)
        article.category = self.insert_category(category_uri)

        tag_uris = self.parse_tags(html)
        article.tags = self.insert_tags(tag_uris)

        article.last_update = date.today()

        return article

    def rename(self, new_path: Path) -> Article:
        """Rename an article in database."""
        # TODO: Set an HTTP redirection (01/2019)
        previous_uri = self.parse_uri()
        article = Article.find(uri=previous_uri)

        self.path = new_path
        new_uri = self.parse_uri()
        article.uri = new_uri

        return self.update()

    def delete(self) -> None:
        """Delete an article from database."""
        uri = self.parse_uri()
        article = Article.find(uri=uri)
        article.delete()

    # Helpers

    def insert_category(self, uri: str) -> Category:
        """Create the article's category, if it doesn't exist yet."""
        category = Category.find(uri=uri)

        if not category:
            name = self.prompt(
                f'Please enter a name for the new "{uri}" category: ')
            category = Category(name=name, uri=uri)
            category.save()

        return category

    def insert_tags(self, uris: Iterable[str]) -> List[Tag]:
        """Create the article's tags, if they don't exist yet."""
        tags = Tag.filter(uri=uris).all()

        existing = set([tag.uri for tag in tags])
        new = set(uris) - existing

        for uri in new:
            name = self.prompt('Please enter a name for the new "{uri}" tag: ')
            tag = Tag(name=name, uri=uri)
            tag.save()
            tags.append(tag)

        return tags

    @staticmethod
    def parse_category(html: BeautifulSoup) -> Optional[str]:
        """Search the category of an article, inside its HTML source."""
        try:
            return html.head.select_one('meta[name=description]')['content']
        except (KeyError, TypeError):
            return None

    @staticmethod
    def parse_content(html: BeautifulSoup) -> Optional[str]:
        """Search the content of an article, inside its HTML source."""
        try:
            return ''.join(str(child) for child in html.body.find_all())
        except AttributeError:
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

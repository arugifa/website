"""Blog file processors."""

from datetime import date

from website.base.processors import BaseDocumentFileProcessor
from website.blog import exceptions
from website.blog.parsers import ArticleSourceParser


class ArticleFileProcessor(BaseDocumentFileProcessor):
    """Process source file of an article."""

    parser = ArticleSourceParser

    async def process(self):
        """Analyze article's source file.

        :return:
            article's attributes, as defined in :class:`website.blog.models.Article`.
        """
        source = await self.load()

        with self.collect_errors() as fp_errors, source.collect_errors() as sp_errors:
            result = {
                'title': source.parse_title(),
                'category': await self.process_category(),
                'lead': source.parse_lead(),
                'body': source.parse_body(),
                'tags': await self.process_tags(),
                'publication_date': self.scan_date(),
            }

        return result, fp_errors | sp_errors

    # Path Scanners

    def scan_date(self) -> date:
        """Return article's creation date, based on its :attr:`path`.

        :raise website.blog.exceptions.ArticleInvalidLocation:
            if the article's parent directoy does not contain a valid year number.
        :raise website.blog.exceptions.ArticleDateMalformatted:
            when the date syntax in article's file's name is incorrect.
        """
        try:
            year = int(self.path.parent.name)
        except ValueError:
            raise exceptions.ArticleInvalidLocation(self)

        try:
            month, day = map(int, self.path.name.split('.')[0].split('-'))
        except (IndexError, TypeError, ValueError):
            raise exceptions.ArticleDateMalformatted(self)

        return date(year, month, day)

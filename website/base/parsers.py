"""Base classes to parse document sources."""

from typing import List

import lxml
import lxml.etree
import lxml.html
from lxml.cssselect import CSSSelector

from website import exceptions


class BaseDocumentSourceParser:
    """Parse HTML source of a document.

    When parsing the document, parsing errors are stored inside :attr:`.errors`.

    :param source:
        document's source.

    :raise website.exceptions.DocumentMalformatted:
        when the given source is not valid HTML.
    """

    def __init__(self, source: str):
        try:
            self._html = lxml.html.document_fromstring(source)
        except lxml.etree.ParserError:
            raise exceptions.DocumentMalformatted(source)

    @property
    def html(self) -> lxml.html.HtmlElement:
        """Document's HTML source. Read only."""
        return self._html

    # Source Parsers

    def parse_category(self) -> str:
        """Look for document's category.

        :raise website.exceptions.DocumentCategoryMissing: when no category is found.
        """
        parser = CSSSelector('html head meta[name=description]')

        try:
            category = parser(self.html)[0].get('content')
            assert category is not None
        except (AssertionError, IndexError):
            raise exceptions.DocumentCategoryMissing(self)

        return category

    def parse_title(self) -> str:
        """Look for document's title.

        :raise website.exceptions.DocumentTitleMissing: when no title is found.
        """
        parser = CSSSelector('html head title')

        try:
            title = parser(self.html)[0].text_content()
            assert title
        except (AssertionError, IndexError):
            raise exceptions.DocumentTitleMissing(self)

        return title

    def parse_tags(self) -> List[str]:
        """Look for document's tags."""
        parser = CSSSelector('html head meta[name=keywords]')

        try:
            tags = parser(self.html)[0].get('content', '')
            tags = [tag.strip() for tag in tags.split(',')]
            assert all(tags)
        except (AssertionError, IndexError):
            return []

        return tags

"""Base classes to parse file sources."""

from typing import Dict, List

import lxml
import lxml.etree
import lxml.html
import yaml
from arugifa.cms.base.parsers import BaseSourceParser
from arugifa.cms.exceptions import SourceMalformatted
from lxml.cssselect import CSSSelector

from website import exceptions


# TODO: Rename to BaseDocumentFileParser (04/2020)
class BaseDocumentSourceParser(BaseSourceParser):
    """Parse HTML source of a document.

    When parsing the document, parsing errors are stored inside :attr:`.errors`.

    :param source:
        document's source.

    :raise website.exceptions.DocumentMalformatted:
        when the given source is not valid HTML.
    """

    @staticmethod
    def deserialize(source) -> lxml.html.HtmlElement:
        try:
            return lxml.html.document_fromstring(source)
        except lxml.etree.ParserError as exc:
            raise SourceMalformatted(exc)

    # Source Parsers

    def parse_category(self) -> str:
        """Look for document's category.

        :raise website.exceptions.DocumentCategoryMissing: when no category is found.
        """
        parser = CSSSelector('html head meta[name=description]')

        try:
            category = parser(self.source)[0].get('content')
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
            title = parser(self.source)[0].text_content()
            assert title
        except (AssertionError, IndexError):
            raise exceptions.DocumentTitleMissing(self)

        return title

    def parse_tags(self) -> List[str]:
        """Look for document's tags."""
        parser = CSSSelector('html head meta[name=keywords]')

        try:
            tags = parser(self.source)[0].get('content', '')
            tags = [tag.strip() for tag in tags.split(',')]
            assert all(tags)
        except (AssertionError, IndexError):
            return []

        return tags


class BaseMetadataFileParser(BaseSourceParser):
    @staticmethod
    def deserialize(source: str) -> Dict:
        try:
            # Use a dict by default, in case source is empty:
            data = yaml.safe_load(source) or {}
            assert isinstance(data, dict), "YAML source must contain a dictionary"
        except (AssertionError, yaml.YAMLError) as exc:
            raise SourceMalformatted(exc)

        return data

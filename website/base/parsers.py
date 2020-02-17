"""Base classes to parse document sources."""

from contextlib import contextmanager
from typing import List

import lxml
import lxml.etree
import lxml.html
from lxml.cssselect import CSSSelector

from website import exceptions
from website.typing import ParsingErrorSet


class CatchParserErrors(type):
    """Meta-class used by all document parsers.

    Catch errors automatically when calling parsing methods.

    This allows to process a document all at once, without having to bother with
    multiple try-catch blocks.
    """

    def __new__(meta, classname, supers, classdict):  # noqa: D102, N804

        def catch_errors(func):
            def wrapper(self, *args, **kwargs):
                try:
                    return func(self, *args, **kwargs)
                except exceptions.DocumentParsingError as exc:
                    if not self._catch_errors:
                        raise

                    self._errors.add(exc)

            return wrapper

        for attr, attrval in classdict.items():
            if attr.startswith('parse_'):
                classdict[attr] = catch_errors(attrval)

        return type.__new__(meta, classname, supers, classdict)


class BaseDocumentSourceParser(metaclass=CatchParserErrors):
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

        self._errors = set()  # To store parsing errors

        # To catch potential exceptions when parsing the document's source.
        self._catch_errors = False

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

    # Helpers

    @contextmanager
    def collect_errors(self) -> ParsingErrorSet:
        """Catch  and return potential errors when parsing document's source.

        Can be used as follows::

            source_file = BaseDocumentSourceParser(file_path)

            with source_file.collect_errors() as errors:
                source_file.parse_title()
                source_file.parse_category()
                source_file.parse_tags()
                print(errors)
        """
        try:
            self._catch_errors = True
            yield self._errors
        finally:
            self._catch_errors = False
            self._errors = set()

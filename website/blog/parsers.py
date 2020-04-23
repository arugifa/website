"""Blog source parsers."""

import re

import lxml.etree
from lxml.cssselect import CSSSelector

from website.base.parsers import BaseDocumentSourceParser
from website.blog import exceptions


class ArticleSourceParser(BaseDocumentSourceParser):
    """Parse HTML source of a blog article."""

    def parse_lead(self) -> str:
        """Look for article's lead paragraph.

        :raise website.blog.exceptions.ArticleLeadMissing:
            when no lead paragraph is found.
        :raise website.blog.exceptions.ArticleLeadMalformatted:
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

        :raise website.blog.exceptions.ArticleBodyMissing: when no body is found.
        """
        parser = CSSSelector('html body div#content div.sect1')
        body = parser(self.source)

        try:
            assert body
        except AssertionError:
            raise exceptions.ArticleBodyMissing(self)

        body = ''.join(lxml.etree.tounicode(section) for section in body)

        return body

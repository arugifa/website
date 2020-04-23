import pytest

from website.blog import exceptions
from website.blog.parsers import ArticleSourceParser
from website.testing.parsers import BaseDocumentSourceParserTest


class TestArticleSourceParser(BaseDocumentSourceParserTest):
    parser = ArticleSourceParser

    @pytest.fixture(scope='class')
    def source(self, fixtures):
        source_file = fixtures['article.html'].open().read()
        return self.parser(source_file)

    # Parse lead.

    def test_parse_lead(self, source):
        lead = source.parse_lead()
        assert lead == "How House Music could save the world?"

    @pytest.mark.parametrize('content', [
        '<div id="preamble"></div>',
        '<div id="preamble"><p></p></div>',
    ])
    def test_parse_missing_lead(self, content):
        html = f'<html><body><div id="content">{content}</div></body></html>'
        with pytest.raises(exceptions.ArticleLeadMissing):
            self.parser(html).parse_lead()

    def test_parse_lead_with_many_paragraphs(self):
        html = (
            '<html><body><div id="content"><div id="preamble">'
            '<p>Paragraph 1</p>'
            '<p>Paragraph 2</p>'
            '</div></div></body></html>'
        )
        with pytest.raises(exceptions.ArticleLeadMalformatted):
            self.parser(html).parse_lead()

    def test_parse_lead_with_new_lines(self):
        html = (
            '<html><body><div id="content">'
            '<div id="preamble"><p>Not enough\nspace?</p></div>'
            '</div></body></html>'
        )
        lead = self.parser(html).parse_lead()
        assert lead == "Not enough space?"

    def test_parse_lead_surrounded_by_new_lines_and_tabulations(self):
        html = (
            '<html><body><div id="content">'
            '<div id="preamble">\n\t<p>\n\t\tLead\n\t\t</p>\n\t</div>'
            '</div></body></html>'
        )
        lead = self.parser(html).parse_lead()
        assert lead == "Lead"

    # Parse body.

    def test_parse_body(self, source):
        actual = source.parse_body()
        expected = (
            '<div class="sect1">\n'
            '<h2 id="_tutorial">Tutorial</h2>\n'
            '<div class="sectionbody">\n'
            '<div class="paragraph">\n'
            '<p>Just move your body.</p>\n'
            '</div>\n</div>\n</div>\n'
            '<div class="sect1">\n'
            '<h2 id="_thats_it">That’s it?</h2>\n'
            '<div class="sectionbody">\n'
            '<div class="paragraph">\n'
            '<p>Feel the vibes…\u200b\nAnd never stop to dance!</p>\n'
            '</div>\n</div>\n</div>\n'
        )
        assert actual == expected

    def test_parse_missing_body(self):
        html = '<html><body><div id="content"></div></body></html>'
        with pytest.raises(exceptions.ArticleBodyMissing):
            self.parser(html).parse_body()

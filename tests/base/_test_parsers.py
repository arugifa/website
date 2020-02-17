import inspect
from typing import ClassVar

import pytest

from website import exceptions
from website.base.parsers import BaseDocumentSourceParser


class BaseDocumentSourceParserTest:
    parser: ClassVar[BaseDocumentSourceParser] = None  # Handler class to test

    # Initialize parser.

    def test_source_must_be_valid_html(self):
        with pytest.raises(exceptions.DocumentMalformatted):
            self.parser('')

    # Collect errors.

    async def test_collect_errors(self):
        parser = self.parser("Invalid document")
        error_count = 0

        with parser.collect_errors() as errors:
            for name, method in inspect.getmembers(parser):
                if name.startswith('parse_'):
                    result = method()  # Should probably raise

                else:
                    continue

                if result is None:
                    error_count += 1

            assert errors
            assert len(errors) == error_count

    # Parse title.

    def test_parse_title(self):
        html = '<html><title>Off-Road Expeditions</title></html>'
        title = self.parser(html).parse_title()
        assert title == 'Off-Road Expeditions'

    @pytest.mark.parametrize('html', [
        '<html></html>',
        '<html><title></title></html>',
    ])
    def test_parse_missing_title(self, html):
        with pytest.raises(exceptions.DocumentTitleMissing):
            self.parser(html).parse_title()

    # Parse category.

    def test_parse_category(self, source):
        category = source.parse_category()
        assert category == 'music'

    @pytest.mark.parametrize('html', [
        '<html><head></head></html>',
        '<html><head><meta name="description"></head></html>',
    ])
    def test_parse_missing_category(self, html):
        with pytest.raises(exceptions.DocumentCategoryMissing):
            self.parser(html).parse_category()

    # Parse tags.

    def test_parse_tags(self):
        html = (
            '<html><head>'
            '<meta name="keywords" content="toyota, land-rover">'
            '</head></html>'
        )
        tags = self.parser(html).parse_tags()
        assert tags == ['toyota', 'land-rover']

    @pytest.mark.parametrize('html', [
        '<html><head></head></html>',
        '<html><head><meta name="keywords"></head></html>',
    ])
    def test_parse_missing_tags(self, html):
        tags = self.parser(html).parse_tags()
        assert tags == []

    def test_parse_empty_tags(self):
        html = '<html><head><meta name="keywords" content=",,"></head></html>'
        tags = self.parser(html).parse_tags()
        assert tags == []

    def test_parse_tags_surrounded_by_spaces(self):
        html = (
            '<html><head>'
            '<meta name="keywords" content="tag1, tag2 , tag3">'
            '</head></html>'
        )
        tags = self.parser(html).parse_tags()
        assert tags == ['tag1', 'tag2', 'tag3']

    def test_parse_tags_not_surrounded_by_spaces(self):
        html = (
            '<html><head>'
            '<meta name="keywords" content="tag1,tag2,tag3">'
            '</head></html>'
        )
        tags = self.parser(html).parse_tags()
        assert tags == ['tag1', 'tag2', 'tag3']

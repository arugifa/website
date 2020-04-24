import pytest
from arugifa.cms import exceptions as cms_errors
from arugifa.cms.testing.parsers import BaseSourceParserTest

from website import exceptions


# TODO: Rename to BaseDocumentFileParserTest (04/2019)
class BaseDocumentSourceParserTest(BaseSourceParserTest):

    # Initialize parser.

    def test_source_must_be_valid_html(self):
        with pytest.raises(cms_errors.SourceMalformatted):
            self.parser('')

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


class BaseMetadataFileParserTest(BaseSourceParserTest):

    # Initialize parser.

    def test_source_must_be_valid_yaml(self):
        with pytest.raises(cms_errors.SourceMalformatted):
            self.parser('{]')

    def test_source_must_be_a_dictionary(self):
        raise NotImplementedError

    def test_can_deserialize_empty_source(self):
        raise NotImplementedError

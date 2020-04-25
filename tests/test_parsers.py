import pytest

from website import exceptions, parsers
from website.testing.parsers import BaseMetadataFileParserTest


class TestCategoriesFileParser(BaseMetadataFileParserTest):
    parser = parsers.CategoriesFileParser

    # Parse categories.

    def test_parse_categories(self):
        yaml = '{"programming": "Software Development", "roadtrip": "Road Trips"}'
        categories = self.parser(yaml).parse_items()

        assert categories == {
            'programming': "Software Development",
            'roadtrip': "Road Trips",
        }

    def test_categories_cannot_be_blank(self):
        with pytest.raises(exceptions.BlankCategories):
            self.parser('').parse_items()

    def test_categorie_names_must_be_strings(self):
        yaml = '{"python": ["py2", "py3"], "rust": null}'

        with pytest.raises(exceptions.InvalidCategoryNames):
            self.parser(yaml).parse_items()


class TestTagsFileParser(BaseMetadataFileParserTest):
    parser = parsers.TagsFileParser

    # Parse tags.

    def test_parse_tags(self):
        yaml = '{"covid19": "Corona Virus", "eow": "End Of the World"}'
        tags = self.parser(yaml).parse_items()

        assert tags == {
            'covid19': "Corona Virus",
            'eow': "End Of the World",
        }

    def test_tag_names_must_be_strings(self):
        yaml = '{"corona": ["covid19", "corosh*t"], "epidemy": null}'

        with pytest.raises(exceptions.InvalidTagNames):
            self.parser(yaml).parse_items()

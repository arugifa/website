from website import parsers
from website.testing.parsers import BaseMetadataFileParserTest


class TestCategoriesFileParser(BaseMetadataFileParserTest):
    parser = parsers.CategoriesFileParser

    # Parse categories.

    def test_parse_categories(self):
        yaml = '{"programming": "Software Development", "roadtrip": "Road Trips"}'
        categories = self.parser(yaml).parse_categories()

        assert categories == {
            'programming': "Software Development",
            'roadtrip': "Road Trips",
        }

    def test_categories_cannot_be_blank(self):
        raise NotImplementedError

    def test_categorie_names_must_be_strings(self):
        raise NotImplementedError


class TestTagsFileParser(BaseMetadataFileParserTest):
    parser = parsers.TagsFileParser

    # Parse tags.

    def test_parse_tags(self):
        yaml = '{"covid19": "Corona Virus", "eow": "End Of the World"}'
        tags = self.parser(yaml).parse_tags()

        assert tags == {
            'covid19': "Corona Virus",
            'eow': "End Of the World",
        }

    def test_tag_names_must_be_strings(self):
        raise NotImplementedError

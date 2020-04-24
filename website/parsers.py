"""Global parsers."""

from typing import Dict

from website import exceptions
from website.base.parsers import BaseMetadataFileParser


class CategoriesFileParser(BaseMetadataFileParser):
    def parse_categories(self) -> Dict:
        if not self.source:
            raise exceptions.BlankCategories

        invalid_categories = []

        for uid, name in self.source.items():
            if not isinstance(name, str):
                invalid_categories.append(uid)

        if invalid_categories:
            raise exceptions.InvalidCategoryNames(invalid_categories)

        return self.source


class TagsFileParser(BaseMetadataFileParser):
    def parse_tags(self) -> Dict:
        invalid_tags = []

        for uid, name in self.source.items():
            if not isinstance(name, str):
                invalid_tags.append(uid)

        if invalid_tags:
            raise exceptions.InvalidTagNames(invalid_tags)

        return self.source

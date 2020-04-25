"""Global file processors."""

from website import parsers
from website.base.processors import BaseMetadataFileProcessor


class CategoriesFileProcessor(BaseMetadataFileProcessor):
    parser = parsers.CategoriesFileParser


class TagsFileProcessor(BaseMetadataFileProcessor):
    parser = parsers.TagsFileParser

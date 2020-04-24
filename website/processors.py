"""Global file processors."""

from website import parsers


class CategoriesFileProcessor:
    parser = parsers.CategoriesParser


class TagsFileProcessor:
    parser = parsers.TagsParser

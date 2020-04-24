"""Global handlers."""

from arugifa.cms.base.handlers import BaseFileHandler

from website import processors
from website.models import Category, Tag


class CategoriesFileHandler(BaseFileHandler):
    processor = processors.CategoriesFileProcessor


class TagsFileHandler(BaseFileHandler):
    processor = processors.TagsFileProcessor

"""Global handlers."""

from website import models, processors
from website.base.handlers import BaseMetadataFileHandler


class CategoriesFileHandler(BaseMetadataFileHandler):
    model = models.Category
    processor = processors.CategoriesFileProcessor


class TagsFileHandler(BaseMetadataFileHandler):
    model = models.Tag
    processor = processors.TagsFileProcessor

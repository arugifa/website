from website import factories, handlers, models
from website.testing.handlers import BaseMetadataFileHandlerTest


class TestCategoriesFileHandler(BaseMetadataFileHandlerTest):
    handler = handlers.CategoriesFileHandler
    model = models.Category
    factory = factories.CategoryFactory


class TestTagsFileHandler(BaseMetadataFileHandlerTest):
    handler = handlers.TagsFileHandler
    model = models.Tag
    factory = factories.TagFactory

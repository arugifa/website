from website import handlers
from website.testing.handlers import BaseMetadataFileHandlerTest


class TestCategoriesFileHandler(BaseMetadataFileHandlerTest):
    handler = handlers.CategoriesFileHandler


class TestTagsFileHandler(BaseMetadataFileHandlerTest):
    handler = handlers.TagsFileHandler

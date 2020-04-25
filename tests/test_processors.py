from website import processors
from website.testing.processors import BaseMetadataFileProcessorTest


class TestCategoriesFileProcessor(BaseMetadataFileProcessorTest):
    processor = processors.CategoriesFileProcessor


class TestTagsFileProcessor(BaseMetadataFileProcessorTest):
    processor = processors.TagsFileProcessor

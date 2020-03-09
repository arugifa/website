from abc import abstractproperty
from pathlib import PurePath

import pytest
from arugifa.cms.testing.processors import BaseFileProcessorTest

from arugifa.website import exceptions
from arugifa.website.factories import CategoryFactory, TagFactory


class BaseDocumentFileProcessorTest(BaseFileProcessorTest):

    @abstractproperty
    @pytest.fixture(scope='class')
    def source_file(self, fixtures):
        return fixtures['document.html']

    # Process category.

    async def test_process_category(self, app, db, tmp_path):
        source_file = tmp_path / 'document_with_category.html'
        source_file.write_text(
            '<html><head><meta name="description" content="travel"></head></html>')

        processor = self.processor(source_file)

        expected = CategoryFactory(uri='travel')
        actual = await processor.process_category()

        assert actual == expected

    async def test_process_missing_category(self, app, db, tmp_path):
        source_file = tmp_path / 'document_without_category.html'
        source_file.write_text("Document with no category")
        processor = self.processor(source_file)

        with pytest.raises(exceptions.DocumentCategoryMissing):
            # TODO: Check category's name in exc (02/2020)
            await processor.process_category()

    async def test_process_unexisting_category(self, app, db, source_file):
        processor = self.processor(source_file)

        with pytest.raises(exceptions.DocumentCategoryNotFound):
            # TODO: Check category's name in exc (02/2020)
            await processor.process_category()

    # Process tags.

    @pytest.mark.parametrize('html', [
        # Tags already sorted.
        '<html><head>''<meta name="keywords" content="greece, portugal">''</head></html>',  # noqa: E501
        # Tags not sorted yet.
        '<html><head>''<meta name="keywords" content="portugal, greece">''</head></html>',  # noqa: E501
    ])
    async def test_process_tags(self, app, db, html, tmp_path):
        source_file = tmp_path / 'document_with_tags.html'
        source_file.write_text(html)

        processor = self.processor(source_file)

        expected = [TagFactory(uri=uri) for uri in ['greece', 'portugal']]
        actual = await processor.process_tags()

        assert actual == expected

    async def test_process_unexisting_tags(self, app, db, source_file):
        processor = self.processor(source_file)

        with pytest.raises(exceptions.DocumentTagsNotFound):
            # TODO: Check tag names in exc (02/2020)
            await processor.process_tags()

    # Scan URI.

    def test_scan_uri(self):
        source_file = PurePath('document.html')
        actual = self.processor(source_file).scan_uri()
        assert actual == 'document'

from abc import abstractproperty
from pathlib import PurePath
from textwrap import dedent
from typing import ClassVar

import pytest
from arugifa.cms import exceptions as cms_errors
from arugifa.cms.testing.processors import BaseFileProcessorTest

from website import exceptions
from website.base import processors
from website.factories import CategoryFactory, TagFactory


@pytest.mark.usefixtures('db')  # For BaseFileProcessorTest's tests to not fail
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


class BaseMetadataFileProcessorTest:
    processor = ClassVar[processors.BaseMetadataFileProcessor]

    # TODO: Test for FileLoadingError here and everywhere else (04/2020)
    async def test_process_file(self, tmp_path):
        # Fixtures
        source_file = tmp_path / 'metadata.yml'
        source_file.write_text(dedent("""
            dev: Development
            photo: Photography
        """))

        # Test
        processor = self.processor(source_file)
        actual = await processor.process()

        expected = {
            'dev': "Development",
            'photo': "Photography",
        }
        assert actual == expected

    async def test_test_process_file_with_errors(self, tmp_path):
        source_file = tmp_path / 'metadata.yml'
        source_file.write_text('{"dev": null}')

        processor = self.processor(source_file)

        with pytest.raises(cms_errors.InvalidFile):
            await processor.process()

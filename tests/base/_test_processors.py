import gzip
import inspect
from abc import ABC, abstractmethod, abstractproperty
from pathlib import PurePath
from typing import ClassVar

import pytest

from website import exceptions
from website.base.processors import BaseDocumentFileProcessor
from website.factories import CategoryFactory, TagFactory


class BaseDocumentFileProcessorTest(ABC):
    processor: ClassVar[BaseDocumentFileProcessor] = None  # Processor class to test

    @abstractproperty
    @pytest.fixture(scope='class')
    def source_file(self, fixtures):
        return fixtures['document.html']

    # Process file.

    @abstractmethod
    def test_process_file(self):
        pass

    # Collect errors.

    async def test_collect_errors(self, app, tmp_path):
        source_file = tmp_path / 'invalid_document.html'
        source_file.write_text("Invalid document")

        processor = self.processor(source_file)
        error_count = 0

        with processor.collect_errors() as errors:
            for name, method in inspect.getmembers(processor):
                if name.startswith('process_'):
                    result = await method()  # Should probably raise

                elif name.startswith('scan_'):
                    result = method()  # Should probably raise

                else:
                    continue

                if result is None:
                    error_count += 1

            assert errors
            assert len(errors) == error_count

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

    # Load document.

    async def test_load_document(self, tmp_path):
        source_file = tmp_path / 'document.html'
        source_file.write_text("Hello, World!")

        processor = self.processor(source_file)
        source = await processor.load()

        assert source.html.text_content() == "Hello, World!"

    async def test_load_not_existing_document(self, tmp_path):
        source_file = tmp_path / 'missing.html'

        with pytest.raises(exceptions.DocumentLoadingError):
            await self.processor(source_file).load()

    async def test_load_not_supported_document_format(self, tmp_path):
        archive = tmp_path / 'document.html.gz'

        with gzip.open(str(archive), 'wb') as f:
            f.write(b'random content')

        with pytest.raises(exceptions.DocumentLoadingError):
            await self.processor(archive).load()

    # Scan URI.

    def test_scan_uri(self):
        source_file = PurePath('document.html')
        actual = self.processor(source_file).scan_uri()
        assert actual == 'document'

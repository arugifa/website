import re

import pytest

from arugifa.cms.testing.readers import BaseReaderTest

from website.readers import AsciidoctorToHTMLConverter


class TestAsciidoctorToHTMLConverter(BaseReaderTest):
    reader = AsciidoctorToHTMLConverter

    # Convert document.

    async def test_convert_document(self, asciidoctor, fixtures):
        document = fixtures['asciidoctor/document.adoc']
        actual = await asciidoctor(document).read()
        expected = fixtures['asciidoctor/document.html'].open().read()

        # Remove timestamp line to avoid flaky tests:
        #
        #     Last updated 2020-02-16 21:05:09 +0100
        #
        regex = re.compile(r'Last updated \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \+\d{4}')
        actual = regex.sub('', actual)
        expected = regex.sub('', expected)

        assert actual == expected

    async def test_convert_document_inside_context_manager(
            self, asciidoctor, fixtures):
        adoc = fixtures['asciidoctor/document.adoc']
        html = fixtures['asciidoctor/document.html']

        async with asciidoctor(adoc) as f:
            actual = await f.read()

        with html.open() as f:
            expected = f.read()

        # Remove timestamp line to avoid flaky tests:
        #
        #     Last updated 2020-02-16 21:05:09 +0100
        #
        regex = re.compile(r'Last updated \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \+\d{4}')
        actual = regex.sub('', actual)
        expected = regex.sub('', expected)

        assert actual == expected

    async def test_error_happening_during_conversion(self, asciidoctor, tmp_path):
        document = tmp_path / 'empty.adoc'
        document.touch()

        adoc = asciidoctor(document)
        document.unlink()

        with pytest.raises(OSError) as excinfo:
            await adoc.read()

        assert "empty.adoc is missing" in str(excinfo.value)

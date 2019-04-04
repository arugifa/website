import pytest

from website.utils.asciidoctor import AsciidoctorToHTMLConverter

from tests._test_content import BaseDocumentReaderTest  # noqa: I100


class TestAsciidoctorToHTMLConverter(BaseDocumentReaderTest):
    reader = AsciidoctorToHTMLConverter

    # Convert document.

    async def test_convert_document(self, asciidoctor, fixtures):
        document = fixtures['document.adoc']
        actual = await asciidoctor(document).read()
        expected = fixtures['document.html'].open().read()
        assert actual == expected

    async def test_convert_document_inside_context_manager(
            self, asciidoctor, fixtures):
        adoc = fixtures['document.adoc']
        html = fixtures['document.html']

        async with asciidoctor(adoc) as f:
            actual = await f.read()

        with html.open() as f:
            expected = f.read()

        assert actual == expected

    async def test_error_happening_during_conversion(
            self, asciidoctor, tmp_path):
        document = tmp_path / 'empty.adoc'
        document.touch()

        adoc = asciidoctor(document)
        document.unlink()

        with pytest.raises(OSError) as excinfo:
            await adoc.read()

        assert "empty.adoc is missing" in str(excinfo.value)

import pytest

from website.utils.asciidoctor import AsciidoctorToHTMLConverter


class TestAsciidoctorToHTMLConverter:
    # Initialize Asciidoctor.

    def test_asciidoctor_not_installed(self, shell):
        def asciidoctor_not_installed():
            raise Exception("Binary not found")

        shell.result = asciidoctor_not_installed

        with pytest.raises(OSError) as excinfo:
            AsciidoctorToHTMLConverter(shell)

        assert "binary not found" in str(excinfo.value)

    # Open document.

    def test_open_not_existing_document(self, asciidoctor):
        with pytest.raises(OSError) as excinfo:
            asciidoctor('missing.adoc')

        assert "doesn't exist" in str(excinfo.value)

    # Read document.

    def test_read_document(self, asciidoctor, fixtures):
        document = fixtures['document.adoc']
        actual = asciidoctor(document).read()
        expected = fixtures['document.html'].open().read()
        assert actual == expected

    def test_read_document_inside_context_manager(self, asciidoctor, fixtures):
        adoc = fixtures['document.adoc']
        html = fixtures['document.html']

        with asciidoctor(adoc) as f1, html.open() as f2:
            actual = f1.read()
            expected = f2.read()

        assert actual == expected

    def test_asciidoctor_cannot_convert_document(self, shell, tmp_path):
        # Fixtures
        class FakeAsciidoctor(AsciidoctorToHTMLConverter):
            def is_installed(self):
                return True

        document = tmp_path / 'empty.adoc'
        document.touch()

        # Test
        def conversion_error():
            raise Exception("Syntax error")

        shell.result = conversion_error
        asciidoctor = FakeAsciidoctor(shell)

        # Assertion
        with pytest.raises(ValueError) as excinfo:
            asciidoctor(document).read()

        assert "Syntax error" in str(excinfo.value)

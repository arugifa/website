from textwrap import dedent

from website.utils.asciidoctor import AsciidoctorToHTMLConverter


def test_convert_asciidoctor(invoke_ctx, tmpdir):
    adoc = tmpdir.join('article.adoc')
    adoc.write("= Hello, World!\n\nThis is a test.")

    converter = AsciidoctorToHTMLConverter(invoke_ctx)
    actual_output = converter(adoc).read()

    expected_output = dedent("""\
        <h1>Hello, World!</h1>
        <div class="paragraph">
        <p>This is a test.</p>
        </div>
        """)

    assert actual_output == expected_output

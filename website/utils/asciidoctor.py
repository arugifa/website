"""Helpers to process website's content written with Asciidoctor.

See https://asciidoctor.org/ to get more insights.
"""

from website.base.readers import BaseDocumentFileReader


class AsciidoctorToHTMLConverter(BaseDocumentFileReader):
    """Asciidoctor to HTML converter, using ``asciidoctor`` command-line tool.

    Can be used as follows::

        convert = AsciidoctorToHTMLConverter()

        with convert(document_path) as html:
            content = html.read()

    For more info about Asciidoctor: https://asciidoctor.org/docs/user-manual/
    """

    program = 'asciidoctor'
    arguments = (
        # Don't use a stylesheet and deactivate warnings.
        '-q -a stylesheet=missing.css '
        # Print the output on stdout.
        '--out-file - {path}'
    )

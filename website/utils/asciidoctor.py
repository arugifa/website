"""Helpers to process website's content written with Asciidoctor.

See https://asciidoctor.org/ to get more insights.
"""

from typing import Callable

from website.content import BaseDocumentReader
from website.exceptions import CommandLineError
from website.utils import BaseCommandLine


class AsciidoctorToHTMLConverter(BaseDocumentReader, BaseCommandLine):
    """Asciidoctor to HTML converter, using ``asciidoctor`` command-line tool.

    Can be used as follows::

        convert = AsciidoctorToHTMLConverter()

        with convert(document_path) as html:
            content = html.read()

    For more info about Asciidoctor: https://asciidoctor.org/docs/user-manual/

    :param shell:
        alternative shell to run ``asciidoctor``. Must have a similar API to
        :func:`subprocess.run`, and raise an exception when executed commands
        exit with a nonzero status code.

    :raise OSError:
        if Asciidoctor is not installed on the machine.
    """

    program = 'asciidoctor'

    def __init__(self, shell: Callable = None):
        BaseDocumentReader.__init__(self)
        BaseCommandLine.__init__(self, shell=shell)  # Can raise OSError

    def read(self) -> str:
        """Read document located at :attr:`path`, using ``asciidoctor``.

        :raise ValueError: if Asciidoctor cannot convert the document.
        """
        cmdline = (
            # Don't use a stylesheet and deactivate warnings.
            f'-q -a stylesheet=missing.css '
            # Print the output on stdout.
            f'--out-file - {self.path}'
        )

        try:
            return self.run(cmdline).strip()
        except CommandLineError as exc:
            raise ValueError(str(exc))

"""Asciidoctor helpers (https://asciidoctor.org/)."""

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

    def __init__(self, shell: Callable = None):
        BaseDocumentReader.__init__(self)
        BaseCommandLine.__init__(self, shell=shell)

        if not self.is_installed():
            raise OSError("Asciidoctor binary not found")

    def read(self) -> str:
        """Read document located at :attr:`path`, using ``asciidoctor``.

        :raise ValueError: if Asciidoctor cannot convert the document.
        """
        cmdline = (
            f'asciidoctor '
            # Don't use a stylesheet and deactivate warnings.
            f'-q -a stylesheet=missing.css '
            # Print the output on stdout.
            f'--out-file - {self.path}'
        )

        try:
            return self.run(cmdline).strip()
        except CommandLineError as exc:
            raise ValueError(str(exc))

    def is_installed(self) -> bool:
        """Check if Asciidoctor is installed on the machine."""
        try:
            self.run('which asciidoctor')
        except CommandLineError:
            return False

        return True

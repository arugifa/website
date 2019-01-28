"""Collection of helpers for Asciidoctor (https://asciidoctor.org/)."""

from typing import Callable

from website.content import BaseDocumentReader
from website.utils import default_runner


class AsciidoctorToHTMLConverter(BaseDocumentReader):
    """Asciidoctor reader with the same API than :func:`open`.

    To be used as follows::

        converter = AsciidoctorToHTMLConverter(subprocess.run)
        content = converter(asciidoctor_file_path).read()

    :param run:
        function to run Asciidoctor in a shell.
        Must have the same API than :func:`subprocess.run`.
    """

    def __init__(self, run: Callable = default_runner):
        super().__init__()
        self.run = run

    def read(self) -> str:
        """Read file located at :attr:`path`, using Asciidoctor."""
        cmdline = (
            'asciidoctor '
            '--no-header-footer '
            '-a showtitle=true '
            '--out-file - '
            f'{self.path}')

        return self.run(cmdline).stdout

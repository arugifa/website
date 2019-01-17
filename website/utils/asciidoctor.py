"""Collection of helpers for Asciidoctor (https://asciidoctor.org/)."""

from pathlib import Path
from typing import Callable, Union

from website.utils import default_runner


class AsciidoctorToHTMLConverter:
    """Asciidoctor reader with the same API than :func:`open`.

    To be used as follows::

        converter = AsciidoctorToHTMLConverter(subprocess.run)
        content = converter(asciidoctor_file_path).read()

    :param run:
        function to run Asciidoctor in a shell.
        Must have the same API than :func:`subprocess.run`.
    """

    def __init__(self, run: Callable = default_runner):
        self.run = run
        #: Path of the Asciidoctor file to read.
        self.path = None

    def __call__(self, path: Union[str, Path]):
        """Prepare the converter for further reading."""
        self.path = path
        return self

    def read(self) -> str:
        """Read file at located at :attr:`path`, using Asciidoctor."""
        cmdline = (
            'asciidoctor '
            '--no-header-footer '
            '-a showtitle=true '
            '--out-file - '
            f'{self.path}')

        return self.run(cmdline).stdout

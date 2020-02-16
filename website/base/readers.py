from abc import ABC
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, ClassVar, Union

from website.base.utils import BaseCommandLine


class BaseDocumentFileReader(ABC, BaseCommandLine):
    """Base class for external document readers.

    Provides a subset of :func:`aiofiles.open`'s API.

    Every reader relies on a :attr:`~program` installed locally, to open, read and if
    necessary convert documents on the fly to HTML format. The result of the conversion
    should be displayed on the standard output.

    :param shell:
        alternative shell to run the reader's :attr:`~program`. Must have a similar API
        to :func:`asyncio.create_subprocess_shell`.
    """

    #: Name of the reader's binary to execute for reading documents.
    program: ClassVar[str] = None
    #: Default arguments to use when running the reader's program.
    arguments: ClassVar[str] = None

    def __init__(self, shell: Callable = None):
        BaseCommandLine.__init__(self, shell)

        #: Path of the document to read. Set by :meth:`__call__`.
        self.path = None

    def __call__(self, path: Union[str, Path]) -> 'DocumentFileOpener':
        """Open the document for further reading.

        Can be called directly or used as a context manager.

        :raise FileNotFoundError: when the document cannot be opened.
        """
        path = Path(path)

        if not path.is_file():
            raise FileNotFoundError(f"Document doesn't exist: {path}")

        self.path = Path(path)
        return DocumentFileOpener(self)

    async def read(self) -> str:
        """Read and convert to HTML the document located at :attr:`path`.

        :raise OSError:
            if the reader's :attr:`~program` cannot convert the document.
        :raise UnicodeDecodeError:
            when the conversion's result is invalid.
        """
        assert self.path is not None, "Open a file before trying to read it"

        cmdline = self.arguments.format(path=self.path)
        # Can raise OSError or UnicodeDecodeError.
        html = await self.run(cmdline)

        return html.strip()


@dataclass
class DocumentFileOpener(AbstractAsyncContextManager):
    """Helper for :class:`BaseDocumentReader` to open documents.

    :param reader: reader instance opening the document.
    """

    reader: BaseDocumentFileReader

    def __getattr__(self, name: str):
        """Let :attr:`reader` opening a document as a function call."""
        return getattr(self.reader, name)

    async def __aenter__(self) -> BaseDocumentFileReader:
        """Let :attr:`reader` opening a document inside a context manager."""
        return self.reader

    async def __aexit__(self, *exc) -> None:
        """Nothing done here for the moment..."""
        return

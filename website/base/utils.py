import asyncio
from functools import partial
from typing import Callable


class BaseCommandLine:
    """Base class to run command lines for a specific program.

    Commands are executed with :func:`asyncio.create_subprocess_shell` by default.

    :param shell:
        alternative to :func:`asyncio.create_subprocess_shell`, with a similar API.
    """

    #: Name of the program's binary to execute.
    program: str = None

    def __init__(self, shell: Callable = None):
        self.shell = shell or partial(
            asyncio.create_subprocess_shell,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def is_installed(self) -> bool:
        """Check if the program is installed on the machine."""
        cmdline = await self.shell(f'which {self.program}')

        # Use communicate() instead of wait(), to avoid potential deadlocks,
        # as stdout/stderr are captured by default when defining self.shell
        _stdout, _stderr = await cmdline.communicate()

        if cmdline.returncode > 0:
            return False

        return True

    async def run(self, options: str) -> str:
        """Run a command, using :attr:`shell`, and return its result.

        :param options: arguments to append to :attr:`program` on the command line.

        :raise OSError: when something wrong happens during command execution.
        :raise UnicodeDecodeError: if it's not possible to decode the command's result.
        """
        cmdline = await self.shell(f'{self.program} {options}')
        stdout, stderr = await cmdline.communicate()

        if cmdline.returncode > 0:
            raise OSError(stderr.decode())  # Can raise UnicodeDecodeError

        return stdout.decode()  # Can raise UnicodeDecodeError

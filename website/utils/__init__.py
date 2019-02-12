"""Collection of helpers to execute command-line tools."""

from functools import partial
from subprocess import run
from typing import Callable

from website.exceptions import CommandLineError


class BaseCommandLine:
    """Base class to run command lines for a specific program.

    Commands are executed with :func:`subprocess.run` by default.

    :param shell:
        alternative to :func:`subprocess.run`, with a similar API. Commands to
        execute are given to this function as strings and not lists. Also, when
        commands exit with a nonzero status code, the function should not fail
        silently, but raises an exception instead.

    :raise OSError:
        if :attr:`program` is not installed on the machine.
    """

    #: Name of the program's binary to execute.
    program: str = None

    def __init__(self, shell: Callable = None):
        self.shell = shell or partial(
            run,
            shell=True,  # Execute command lines as strings and not lists
            check=True,  # Verify status code
            capture_output=True,  # Store stdout and stderr
            text=True,  # Decode stdout and stderr
        )

        if not self.is_installed():
            raise OSError(f"{self.program.title()} binary not found")

    def is_installed(self) -> bool:
        """Check if the program is installed on the machine."""
        try:
            self.shell(f'which {self.program}')
        except Exception:
            return False

        return True

    def run(self, options: str) -> str:
        """Run a command, using :attr:`shell`, and return its result.

        :param options:
            arguments to append to :attr:`program` on the command line.
        :raise ~.CommandLineError:
            when something wrong happens.
        """
        cmdline = f'{self.program} {options}'

        try:
            return self.shell(cmdline).stdout
        except Exception as exc:
            raise CommandLineError(exc)

"""Collection of helpers to be used when running integration tests."""
# TODO: Finish to write docstrings, after having agreed on a final API (05/2019)

import asyncio
import re
from subprocess import Popen, run
from typing import Callable, Mapping, Tuple, Union

from arugifa.toolbox.cli.base import BaseCommandLine
from faker import Faker

from website.test.stubs import stub


ShellStatusCode = int
ShellOutput = Union[str, Callable]
ShellResult = Union[ShellOutput, Tuple[ShellOutput, ShellStatusCode]]

fake = Faker()


class Sass(BaseCommandLine):
    program = 'sassc'


class CommandLine:
    """Execute an external program in tests with :mod:`subprocess`.

    The main difference with :class:`.TestingShell` is that this latter is meant to
    execute programs from the codebase. But :class:`.CommandLine` is meant to execute
    programs inside the tests themselves.
    """

    def __init__(self, program):
        self.program = program

    def run(self, arguments, **kwargs):
        """Run a command-line with :func:`subprocess.run`."""
        cmdline = self._get_command_line(arguments)
        return run(cmdline, **kwargs)

    def run_with_popen(self, arguments, **kwargs):
        """Run a command-line with :class:`subprocess.Popen`."""
        cmdline = self._get_command_line(arguments)
        return Popen(cmdline, **kwargs)

    def _get_command_line(self, arguments):
        cmdline = arguments.split()
        cmdline.insert(0, self.program)
        return cmdline


@stub(asyncio.create_subprocess_shell)
class TestingShell:
    """Shell to be injected in the codebase when external programs must be executed."""

    def __init__(self):
        self._result = None

    # Original methods and attributes.

    async def __call__(self, cmdline: str) -> 'TestingShell':
        return self

    @property
    def stdout(self):
        stdout = self._result[0]
        return stdout if not stdout else stdout()

    @property
    def stderr(self):
        stderr = self._result[1]
        return stderr if not stderr else stderr()

    @property
    def returncode(self):
        return self._result[2]

    # Stub methods and attributes.

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value: ShellResult):
        """...

        :param value:
            the result of the executed command (output + status code).
            Instead of a string, a function can be used to dynamically generate
            the output, which can be useful to trigger side-effects
            (e.g., raising an exception). Also, if the status code is not null,
            then the output is assigned to :attr:`~stderr`, and not
            :attr:`~stdout`.
        """
        if isinstance(value, tuple):
            output, status = value
        else:
            output = value
            status = 0

        if callable(output):
            result = output
        elif isinstance(output, str):
            result = (lambda: output.encode())
        else:  # Bytes
            result = (lambda: output)

        if status == 0:
            stdout = result
            stderr = b''
        else:
            stdout = b''
            stderr = result

        self._result = (stdout, stderr, status)

    async def communicate(self) -> Tuple[str, None]:
        return self.stdout, self.stderr

    async def wait(self) -> int:
        return self.returncode

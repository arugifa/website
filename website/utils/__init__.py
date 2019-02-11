"""Collection of helpers to execute command-line tools."""

import os
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from subprocess import run
from typing import Callable, ContextManager

from website.exceptions import CommandLineError


class BaseCommandLine:
    """Base class for running command lines.

    Commands are executed with :func:`subprocess.run` by default.

    :param shell:
        alternative to :func:`subprocess.run`, with a similar API.
        Commands to execute are given to this function as strings and not lists.
        Also, when commands exit with a nonzero status code, the function should
        not fail silently, but raises an exception instead.
    """  # noqa: E501

    def __init__(self, shell: Callable = None):
        self.shell = shell or partial(
            run,
            shell=True,  # Execute command lines as strings and not lists
            check=True,  # Verify status code
            capture_output=True,  # Store stdout and stderr
            text=True,  # Decode stdout and stderr
        )

    @contextmanager
    def cwd(self, path: Path) -> ContextManager:
        """Temporarily change the current working directory to ``path``."""
        cwd = os.getcwd()

        try:
            os.chdir(path)
        finally:
            os.chdir(cwd)

    def run(self, cmdline: str) -> str:
        """Run a command, using :attr:`shell`, and return its result.

        :raise ~.CommandLineError: when something wrong happens.
        """
        try:
            return self.shell(cmdline).stdout
        except Exception as exc:
            raise CommandLineError(exc)

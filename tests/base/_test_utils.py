"""Base classes to test command line programs."""

from abc import ABC, abstractmethod
from functools import partial
from hashlib import sha1
from typing import Union

import pytest

from website.base.utils import BaseCommandLine


class BaseCommandLineTest(ABC):
    @abstractmethod
    @pytest.fixture
    def program_factory(self) -> Union[BaseCommandLine, partial]:
        """Initialize with default parameters the command-line utility to test.

        Meant to be used by test methods defined in this base class.
        """

    # Is the program installed?

    async def test_program_is_installed(self, program_factory, shell):
        program = program_factory(shell=shell)
        shell.result = f"/usr/bin/{program.program}"
        installed = await program.is_installed()
        assert installed is True

    async def test_program_is_not_installed(self, program_factory, shell):
        program = program_factory(shell=shell)
        shell.result = (f"no {program.program} in /usr/bin", 1)
        installed = await program.is_installed()
        assert installed is False

    # Run program.

    async def test_running_error(self, program_factory, shell):
        program = program_factory(shell=shell)
        shell.result = ("Große Katastrophe!!!", 1)

        with pytest.raises(OSError) as excinfo:
            await program.run('BOUM!')

        assert "Katastrophe" in str(excinfo)

    async def test_result_decoding_error(self, program_factory, shell):
        program = program_factory(shell=shell)
        shell.result = sha1(b"Nich Gut!").digest()

        with pytest.raises(UnicodeDecodeError):
            await program.run('BADABOUM!')

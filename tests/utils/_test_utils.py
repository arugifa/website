from abc import ABC, abstractmethod
from functools import partial

import pytest


class BaseCommandLineTest(ABC):
    @abstractmethod
    @pytest.fixture(scope='class')
    def default(self) -> partial:
        """Initialize with default parameters the command-line utility to test.

        Only meant to be used by methods defined in this base test class.
        """

    # Initialize command-line utility.

    def test_program_not_installed(self, default, shell):
        def program_not_installed():
            raise Exception("Binary not found")

        shell.result = program_not_installed

        with pytest.raises(OSError) as excinfo:
            default(shell=shell)

        assert "binary not found" in str(excinfo.value)

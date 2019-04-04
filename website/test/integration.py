import asyncio
import re
import shlex
import shutil
from collections.abc import Mapping as AbstractMapping
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from subprocess import PIPE, Popen, run
from typing import Callable, Mapping, Tuple, Union

from faker import Faker
from _pytest.fixtures import FixtureRequest

from website.content import WebsiteContentPrompt
from website.stubs import stub


ShellStatusCode = int
ShellOutput = Union[str, Callable]
ShellResult = Union[ShellOutput, Tuple[ShellOutput, ShellStatusCode]]

fake = Faker()


class CommandLine:
    """Execute a program with :mod:`subprocess`."""

    def __init__(self, program):
        self.program = program

    def get_command_line(self, arguments):
        cmdline = arguments.split()
        cmdline.insert(0, self.program)
        return cmdline

    def run(self, arguments, **kwargs):
        cmdline = self.get_command_line(arguments)
        return run(cmdline, **kwargs)

    def run_with_popen(self, arguments, **kwargs):
        cmdline = self.get_command_line(arguments)
        return Popen(cmdline, **kwargs)


@dataclass
class FileFixtureCollection(AbstractMapping):
    directory: Path
    # TODO: Remove request, we don't use it (03/2019)
    request: FixtureRequest
    # TODO: Rename to hardlinks (03/2019)
    symlinks: Path

    def __getitem__(self, key: str) -> 'FileFixture':
        return FileFixture(self.directory / key, collection=self)

    def __iter__(self) -> str:
        return iter(
            str(path.relative_to(self.directory))
            for path in self.directory.rglob('*')
        )

    def __len__(self) -> int:
        return len(self.directory.rglob('*'))


@dataclass
class FileFixture(PathLike):
    """...

    :param path: fixture's path.
    :param collection: set of fixtures to which belongs the fixture.
    """
    path: Path
    collection: FileFixtureCollection

    def __fspath__(self):
        return str(self.path)

    def __getattr__(self, name):
        return getattr(self.path, name)

    def __str__(self):
        return str(self.path)

    def copy(self, target: Union[str, Path], shallow: bool = False) -> 'FileFixture':
        target = Path(target)

        if not target.is_absolute():
            target = self.collection.symlinks / target

        if target.exists():  # To be used with session-scoped fixtures
            target.unlink()
        elif not target.parent.exists():
            target.parent.mkdir(parents=True)

        if shallow:
            target.symlink_to(self.path)
        else:
            shutil.copyfile(self.path, target)

        return FileFixture(target, self.collection)

    def move(self, target: Union[str, Path]) -> None:
        self.path = self.symlink(target).path

    def symlink(self, target: Union[str, Path]) -> 'FileFixture':
        return self.copy(target, shallow=True)


class InvokeStub:
    """To be injected in functions or methods depending on Invoke context."""

    @staticmethod
    def run(cmdline, **kwargs):
        cmdline = cmdline.split()
        return run(cmdline, stdout=PIPE, universal_newlines=True)


class TestingPromptInput:
    def __init__(self):
        self.answers = {}

    @stub(input, classified=True)
    def __call__(self, prompt=None):
        for question, answer in self.answers.items():
            if question.search(prompt):
                return answer

        return fake.word()


class TestingPrompt(WebsiteContentPrompt):
    def __init__(self):
        input = TestingPromptInput()
        WebsiteContentPrompt.__init__(self, input=input)

    def add_answers(self, answers: Mapping[str, str]) -> None:
        self.input.answers.update({
            re.compile(question): answer
            for question, answer in answers.items()
        })


"""
class Shell(AbstractMutableMapping):
    def __init__(self):
        self.commands = {}

    def __bool__(self):
        return True

    def __call__(self, cmdline: str) -> str:
        for command, result in self.commands.items():
            if command.search(cmdline):
                return result()

        return OSError("Command not found")

    def __delitem__(self, key: str) -> None:
        del self.commands[key]

    def __getitem__(self, key: str) -> Callable:
        return self.commands[key]

    def __iter__(self):
        return iter(self.commands)

    def __len__(self):
        return len(self.commands)

    def __setitem__(self, key: str, value: Union[str, Callable]) -> None:
        command = re.compile(key)
        result = (lambda: value) if isinstance(value, str) else value
        self.commands[command] = result
"""


@stub(asyncio.create_subprocess_shell)
class TestingShell:
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


class RunStub:
    def __init__(self):
        self.output = None
        self.stdout = None

    def __call__(self, cmdline):
        self.stdout = self.output
        self.output = None
        return self


class RunReal:
    def __init__(self):
        self.output = None

    def __call__(self, cmdline):
        cmdline = shlex.split(cmdline)
        process = run(cmdline, check=True, stdout=PIPE, encoding='utf-8')

        if self.output:
            assert process.stdout == self.output
            self.output = None

        return process

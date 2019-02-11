import re
import shlex
from collections import defaultdict
from collections.abc import (
    Mapping as AbstractMapping, MutableMapping as AbstractMutableMapping)
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from subprocess import PIPE, Popen, run
from typing import Callable, Mapping, Union

from faker import Faker
from _pytest.fixtures import FixtureRequest

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
    request: FixtureRequest
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

    def copy(self, target):
        new_path = self.collection.symlinks / target

        if new_path.exists():
            new_path.unlink()
        elif not new_path.parent.exists():
            new_path.parent.mkdir(parents=True)

        new_path.symlink_to(self.path)
        return FileFixture(new_path, self.collection)

    def rename(self, target):
        self.path = self.copy(target).path
        return self


class InvokeStub:
    """To be injected in functions or methods depending on Invoke context."""

    @staticmethod
    def run(cmdline, **kwargs):
        cmdline = cmdline.split()
        return run(cmdline, stdout=PIPE, universal_newlines=True)


class Prompt:
    def __init__(self):
        self.answers = {}

    def __call__(self, text: str) -> str:
        for question, answer in self.answers.items():
            if question.search(text):
                return answer

        return fake.word()

    def add_answers(self, answers: Mapping[str, str]) -> None:
        self.answers.update({
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


class Shell:
    def __init__(self):
        self._result = None

    def __call__(self, cmdline: str) -> str:
        return self._result()

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        value = (lambda: value) if isinstance(value, str) else value
        self._result = value


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

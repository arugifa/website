import re
import shlex
from collections.abc import Mapping as AbstractMapping
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from subprocess import PIPE, Popen, run
from typing import Mapping

from faker import Faker

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

    def copy(self, target):
        new_path = self.collection.symlinks / target

        if not new_path.parent.exists():
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

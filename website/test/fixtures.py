"""Load user-defined text fixtures from local disk.

Avoid to store a bunch of huge text strings inside test definitions.
"""
# TODO: Finish to write docstrings, after having agreed on a final API (05/2019)

import shutil
from collections.abc import Mapping as AbstractMapping
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Union


@dataclass
class FileFixtureCollection(AbstractMapping):
    """Retrieve fixtures stored in local files."""

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
    """Manipulate a local file fixture to be reused between tests.

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
        """Copy the fixture.

        :param target: name of the copy.
        :param shallow: set to ``True`` to make a symlink instead of a real copy.
        """
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
            if self.path.is_file():
                shutil.copyfile(self.path, target)
            else:
                shutil.copytree(self.path, target)

        return FileFixture(target, self.collection)

    # TODO: Rename to rename() (01/2020)
    def move(self, target: Union[str, Path]) -> None:
        self.path = self.symlink(target).path

    def rename(self, target: Union[str, Path]) -> None:
        self.path = self.symlink(target).path

    # TODO: Remove and rename copy() to copy(target, symlink=True/False)
    def symlink(self, target: Union[str, Path]) -> 'FileFixture':
        return self.copy(target, shallow=True)

"""Helpers to identify changes, with Git, in the website's content."""

import hashlib
from pathlib import Path
from typing import Callable, Dict, Iterable, Union

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError

from website import exceptions
from website.utils import BaseCommandLine


# TODO: Rename to GitRepository (03/2019)
class Repository(BaseCommandLine):
    """Wrapper around :class:`git.Repo` to provide a nicer API.

    This is especially true for :meth:`Repo.diff`, but other methods have also
    been rewritten:

    - to simulate how Git is used on the command-line,
    - and decouple tests from code implementation
      (so the tests don't depend directly on :mod:`git`).

    :param path:
        repository's path.
    :param shell:
        alternative shell to interact with ``git``. Must have a similar API to
        :func:`subprocess.run`, and raise an exception when executed commands
        exit with a nonzero status code.
    :raise ~.RepositoryNotFound:
        if no repository exists at ``path``.
    """

    program = 'git'

    def __init__(self, path: Union[str, Path], shell: Callable = None):
        BaseCommandLine.__init__(self, shell=shell)

        try:
            self._repo = Repo(path)
        except (NoSuchPathError, InvalidGitRepositoryError):
            raise exceptions.RepositoryNotFound(path)

        self.path = Path(path)

    @classmethod
    def init(cls, directory: Union[str, Path]) -> 'Repository':
        """Create a new repository, located at ``directory``."""
        Repo.init(directory, mkdir=True)
        return cls(directory)

    def add(self, *files: Union[str, Path]) -> None:
        """Add files to the repository's index.

        By default, adds all untracked files and unstaged changes to the index.
        """
        if files:
            self._repo.index.add(map(str, files))
        else:
            # Add all untracked files (i.e., new or renamed files).
            self._repo.index.add(self._repo.untracked_files)

            # Add all changes not staged for commit.
            for change in self._repo.index.diff(None):
                try:
                    # Added or modified files.
                    self._repo.index.add([change.a_blob.path])
                except FileNotFoundError:
                    # Deleted or renamed files.
                    self._repo.index.remove([change.a_blob.path])

    # TODO: Add test (03/2019)
    def remove(self, *files: Union[str, Path]) -> None:
        self._repo.index.remove(map(str, files))

    # TODO: Add test (03/2019)
    def move(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        self._repo.index.move([str(src), str(dst)])

    def commit(self, message: str) -> str:
        """Commit files added to the repository's index.

        :param message: commit message.
        :return: the commit's hash.
        """
        commit = self._repo.index.commit(message)
        return hashlib.sha1(commit.binsha).hexdigest()

    def diff(
            self, from_commit: str,
            to_commit: str = 'HEAD') -> Dict[str, Iterable[Path]]:
        """Return changes between two commits.

        :param from_commit: hash of the reference commit.
        :param to_commit: hash of the commit to compare to.

        :return: ``added``, ``modified``, ``renamed`` and ``deleted`` files.
        """
        diff = self._repo.commit(from_commit).diff(to_commit)

        pretty_diff = {
            'added': sorted(
                Path(d.b_blob.path)
                for d in diff.iter_change_type('A')
            ),
            'modified': sorted(
                Path(d.b_blob.path)
                for d in diff.iter_change_type('M')
            ),
            'renamed': sorted(
                (Path(d.a_blob.path), Path(d.b_blob.path))
                for d in diff.iter_change_type('R')
            ),
            'deleted': sorted(
                Path(d.a_blob.path)
                for d in diff.iter_change_type('D')
            ),
        }

        return pretty_diff

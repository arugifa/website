import os
from functools import partial
from io import StringIO
from pathlib import Path
from textwrap import dedent

import pytest

from website.utils.git import Repository

from tests.utils._test_utils import BaseCommandLineTest  # noqa: I100


class TestRepository(BaseCommandLineTest):

    @pytest.fixture(scope='class')
    def default(self, git):
        return partial(Repository, 'empty')

    @pytest.fixture(scope='class')
    def repository(self, git, tmp_path_factory):
        cwd = os.getcwd()
        tmpdir = tmp_path_factory.mktemp('test_repository')

        try:
            os.chdir(tmpdir)

            # Initialize repository.
            repo = git.init(tmpdir)

            readme = tmpdir / 'README.txt'
            readme.touch()

            repo.add([readme])
            repo.commit("HEAD~3")

            # Populate repository with non-empty files,
            # otherwise Git can be lost with file names later on.
            to_modify = tmpdir / 'modified.txt'
            to_modify.write_text('to modify')

            to_delete = tmpdir / 'deleted.txt'
            to_delete.write_text('to delete')

            to_rename = tmpdir / 'to_rename.txt'
            to_rename.write_text('to rename')

            repo.add([to_modify, to_delete, to_rename])
            repo.commit("HEAD~2")

            # Proceed to some changes.
            to_delete.unlink()

            renamed = tmpdir / 'renamed.txt'
            to_rename.rename(renamed)

            to_modify.write_text('modified')

            added = tmpdir / 'added.txt'
            added.write_text('added')

            repo.add()
            repo.commit("HEAD~1")

            # Make one last commit,
            # to be able to compare not subsequent commits.
            new = tmpdir / 'new.txt'
            new.write_text('new')

            repo.add([new])
            repo.commit("HEAD")

        finally:
            os.chdir(cwd)

        return repo

    # Git diff.

    def test_diff_between_two_specific_commits(self, git, repository):
        actual = repository.diff('HEAD~2', 'HEAD~1')

        expected = {
            'added': [Path('added.txt')],
            'modified': [Path('modified.txt')],
            'renamed': [(Path('to_rename.txt'), Path('renamed.txt'))],
            'deleted': [Path('deleted.txt')],
        }
        assert actual == expected

    def test_diff_from_one_specific_commit_to_head(self, repository):
        actual = repository.diff('HEAD~2')

        expected = {
            'added': [Path('added.txt'), Path('new.txt')],
            'modified': [Path('modified.txt')],
            'renamed': [(Path('to_rename.txt'), Path('renamed.txt'))],
            'deleted': [Path('deleted.txt')],
        }
        assert actual == expected

    def test_diff_with_changes_lost_between_not_subsequent_commits(
            self, git, repository):
        actual = repository.diff('HEAD~3')

        expected = {
            'added': [
                Path('added.txt'),
                Path('modified.txt'),
                Path('new.txt'),
                Path('renamed.txt'),
            ],
            'modified': [],
            'renamed': [],
            'deleted': [],
        }
        assert actual == expected

    def test_print_diff(self, repository):
        stream = StringIO()
        repository.diff('HEAD~2', quiet=False, output=stream)

        assert stream.getvalue() == dedent("""\
            The following files have been added:
            - added.txt
            - new.txt
            The following files have been modified:
            - modified.txt
            The following files have been renamed:
            - to_rename.txt -> renamed.txt
            The following files have been deleted:
            - deleted.txt
        """)

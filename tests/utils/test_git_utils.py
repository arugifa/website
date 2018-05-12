from textwrap import dedent

import pytest

from website.utils import git


class TestGetDiff():
    @pytest.fixture(scope='class')
    def repository(self, shell, tmpdir_factory):
        tmpdir = tmpdir_factory.mktemp('test_get_diff')

        shell(f'git init {tmpdir}')
        tmpdir.ensure('init.txt')

        shell(f'git add {tmpdir}')
        shell('git commit -m "First commit"')

        # Populate repository.
        modified = tmpdir.ensure('modified.txt')
        renamed = tmpdir.ensure('to_rename.txt')
        # To not be confused with empty added/deleted files.
        renamed.write('renamed')
        deleted = tmpdir.ensure('deleted.txt')
        # To not be confused with empty added/renamed files.
        deleted.write('deleted')

        shell(f'git add {tmpdir}')
        shell('git commit -m "Second commit"')

        # Proceed to some changes.
        deleted.remove()
        renamed.rename('renamed.txt')
        modified.write('modified')
        tmpdir.ensure('added.txt')

        shell(f'git add {tmpdir}')
        shell('git commit -m "Third commit"')

        # Make another commit, to have more than 2 commits.
        tmpdir.ensure('new.txt')
        shell(f'git add {tmpdir}')
        shell('git commit -m "Last commit"')

    def test_get_diff_using_head(self, repository, shell):
        shell.output = dedent("""\
            A       added
            D       deleted
            M       modified
            A       new
            R100    to_rename       renamed
        """)

        actual = git.get_diff(shell, 'HEAD~2')
        expected = (
            ['added.txt', 'new.txt'],
            ['modified.txt'],
            ['renamed.txt'],
            ['deleted.txt'],
        )
        assert actual == expected

    def test_get_diff_between_two_commits(self, repository, shell):
        shell.output = dedent("""\
            A       added
            D       deleted
            M       modified
            R100    to_rename       renamed
        """)

        actual = git.get_diff(shell, 'HEAD~2', 'HEAD~1')
        expected = (
            ['added.txt'],
            ['modified.txt'],
            ['renamed.txt'],
            ['deleted.txt'],
        )
        assert actual == expected

    def test_get_partial_diff(self, repository, shell):
        shell.output = dedent("""\
            A       added
            A       modified
            A       new
            A       renamed
        """)

        actual = git.get_diff(shell, 'HEAD~3')
        expected = (
            ['added.txt', 'deleted.txt', 'modified.txt', 'renamed.txt'],
            [],
            [],
            [],
        )
        assert actual == expected

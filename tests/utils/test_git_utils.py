from io import StringIO
from textwrap import dedent

import pytest

from website.utils import git as git_utils


class TestGetDiff():
    @pytest.fixture(scope='class')
    def repository(self, shell, tmpdir_factory):
        tmpdir = tmpdir_factory.mktemp('test_get_diff')

        with tmpdir.as_cwd():
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
            renamed.rename(tmpdir.join('renamed.txt'))
            modified.write('modified')
            tmpdir.ensure('added.txt')

            shell(f'git add {tmpdir}')
            shell('git commit -m "Third commit"')

            # Make another commit, to have more than 2 commits.
            tmpdir.ensure('new.txt')
            shell(f'git add {tmpdir}')
            shell('git commit -m "Last commit"')

        return tmpdir

    def test_get_diff_using_head(self, git, monkeypatch, repository):
        git.output = dedent("""\
            A\tadded.txt
            D\tdeleted.txt
            M\tmodified.txt
            A\tnew.txt
            R100\tto_rename.txt\trenamed.txt
        """)

        monkeypatch.chdir(repository)
        actual = git_utils.get_diff('HEAD~2', shell=git)

        expected = (
            ['added.txt', 'new.txt'],
            ['modified.txt'],
            [('to_rename.txt', 'renamed.txt')],
            ['deleted.txt'],
        )
        assert actual == expected

    def test_get_diff_between_two_commits(self, git, monkeypatch, repository):
        git.output = dedent("""\
            A\tadded.txt
            D\tdeleted.txt
            M\tmodified.txt
            R100\tto_rename.txt\trenamed.txt
        """)

        monkeypatch.chdir(repository)
        actual = git_utils.get_diff('HEAD~2', 'HEAD~1', shell=git)

        expected = (
            ['added.txt'],
            ['modified.txt'],
            [('to_rename.txt', 'renamed.txt')],
            ['deleted.txt'],
        )
        assert actual == expected

    def test_get_partial_diff(self, git, monkeypatch, repository):
        git.output = dedent("""\
            A\tadded.txt
            A\tmodified.txt
            A\tnew.txt
            A\trenamed.txt
        """)

        monkeypatch.chdir(repository)
        actual = git_utils.get_diff('HEAD~3', shell=git)

        expected = (
            ['added.txt', 'modified.txt', 'new.txt', 'renamed.txt'],
            [],
            [],
            [],
        )
        assert actual == expected


def test_print_diff():
    diff = (
        ['added_1', 'added_2'],
        ['modified_1', 'modified_2'],
        [('to_rename_1', 'renamed_1'), ('to_rename_2', 'renamed_2')],
        ['deleted_1', 'deleted_2'],
    )

    stream = StringIO()
    git_utils.print_diff(stream, diff)

    assert stream.getvalue() == dedent("""\
        The following files have been added:
        - added_1
        - added_2
        The following files have been modified:
        - modified_1
        - modified_2
        The following files have been renamed:
        - to_rename_1 -> renamed_1
        - to_rename_2 -> renamed_2
        The following files have been deleted:
        - deleted_1
        - deleted_2
    """)

from functools import partial
from pathlib import Path

import pytest

from website import exceptions
from website.utils.git import Repository

from tests.utils._test_utils import BaseCommandLineTest  # noqa: I100


class TestRepository(BaseCommandLineTest):

    @pytest.fixture
    def program_factory(self, git, tmp_path):
        repo = git.init(tmp_path)
        return partial(Repository, repo.path)

    @pytest.fixture(scope='class')
    def repository(self, git, tmp_path_factory):
        tmpdir = tmp_path_factory.mktemp(self.__class__.__name__)

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

        return repo

    # Initialize repository.

    def test_directory_missing(self, tmp_path):
        with pytest.raises(exceptions.RepositoryNotFound):
            Repository(tmp_path / 'nothing')

    def test_repository_not_initialized(self, tmp_path):
        with pytest.raises(exceptions.RepositoryNotFound):
            Repository(tmp_path)

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

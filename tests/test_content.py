from datetime import date
from pathlib import PurePath
from random import random

import pytest

from website import exceptions
from website.blog.content import ArticleHandler
from website.blog.factories import ArticleFactory
from website.content import ContentUpdateManager


class TestContentUpdateManager:

    '''
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
    '''

    @pytest.fixture(scope='class')
    def handlers(self):
        return {'blog': ArticleHandler}

    @pytest.fixture(scope='class')
    def changes(self, repository):
        return repository.diff('HEAD~4')

    @pytest.fixture(scope='class')
    def repository(self, fixtures, git, tmp_path_factory):
        article = fixtures['blog/article.html']
        tmpdir = tmp_path_factory.mktemp(self.__class__.__name__)

        # Initialize repository.
        repo = git.init(tmpdir)

        to_rename = self.copy(article, repo.path / 'blog/to_rename.html')
        to_modify = self.copy(article, repo.path / 'blog/modified.html')
        to_delete = self.copy(article, repo.path / 'blog/deleted.html')
        import pdb
        pdb.set_trace()

        repo.add(to_rename, to_modify, to_delete)
        repo.commit('HEAD~4')

        # Add documents.
        added = self.copy(article, repo.path / 'blog/added.html')
        repo.add(added)
        repo.commit('HEAD~3')

        # Rename documents.
        repo.move(to_rename, repo.path / 'blog/renamed.html')
        repo.commit('HEAD~2')

        # Modify documents.
        with to_modify.open('a') as f:
            f.write('modification')

        repo.add(to_modify)
        repo.commit('HEAD~1')

        # Delete documents.
        repo.remove(to_delete)
        repo.commit('HEAD')

        import pdb
        pdb.set_trace()
        return repo

    # XXX: Set prompt's scope to class? (03/2019)
    @pytest.fixture
    def content(self, repository, handlers, prompt):
        return ContentUpdateManager(repository, handlers, prompt=prompt)

    def copy(self, src, dst):
        document = src.copy(dst)

        with document.open('a') as f:
            stamp = random()
            f.write(f"{stamp}")

        return document

    # Update content.

    # TODO: Update at least 2 different kinds of documents (02/2019)
    # Because that's how the content manager is intended to behave...
    async def test_update_content(self, repository, content, db, fixtures):
        # Fixtures
        to_delete = ArticleFactory(uri='deleted')

        to_modify = ArticleFactory(uri='modified')
        assert to_modify.last_update is None

        to_rename = ArticleFactory(uri='to_rename')
        assert to_rename.last_update is None

        # Test
        documents = await content.update(repository).run()

        # Assertions
        assert len(documents) == 3

        assert documents[0].uri == 'added'

        assert documents[1].uri == 'modified'
        assert documents[1].last_update == date.today()

        assert documents[2].uri == 'renamed'
        assert documents[2].last_update == date.today()

        assert to_delete.exists() is False

    # Add documents.

    # TODO: Add at least 2 documents of different kinds (02/2019)
    # Because that's how the content manager is intended to behave...
    def test_add_documents(self, changes, content, db):
        documents = content.add(changes['added'])
        assert len(documents) == 1
        assert documents[0].uri == 'to_add'

    def test_add_already_existing_document(self, changes, content, db):
        ArticleFactory(uri='to_add')

        with pytest.raises(exceptions.ItemAlreadyExisting):
            content.add(changes['added'])

    def test_add_document_with_missing_handler(self, content):
        source = PurePath('blog_articles/article.html')

        with pytest.raises(exceptions.HandlerNotFound):
            content.add([source])

    def test_add_document_stored_in_another_directory(self, content):
        source = PurePath('/invalid/article.html')

        with pytest.raises(exceptions.InvalidDocumentLocation):
            content.add([source])

    # Modify documents.

    # TODO: Modify at least 2 documents of different kinds (02/2019)
    # Because that's how the content manager is intended to behave...
    def test_modify_documents(self, changes, content, db):
        article = ArticleFactory(uri='to_modify')
        assert article.last_update is None

        documents = content.refresh(changes['modified'])

        assert len(documents) == 1
        assert documents[0] is article
        assert documents[0].last_update == date.today()

    def test_modify_not_existing_document(self, changes, content, db):
        with pytest.raises(exceptions.ItemNotFound):
            content.refresh(changes['modified'])

    def test_modify_document_with_missing_handler(self, content):
        source = PurePath('blog_articles/article.html')

        with pytest.raises(exceptions.HandlerNotFound):
            content.refresh([source])

    def test_modify_document_stored_in_another_directory(self, content):
        source = PurePath('/invalid/article.html')

        with pytest.raises(exceptions.InvalidDocumentLocation):
            content.refresh([source])

    # Rename documents.

    # TODO: Rename at least 2 documents of different kinds (02/2019)
    # Because that's how the content manager is intended to behave...
    def test_rename_documents(self, changes, content, db):
        article = ArticleFactory(uri='to_rename')
        assert article.last_update is None

        documents = content.rename(changes['renamed'])

        assert len(documents) == 1
        assert documents[0] is article
        assert documents[0].uri == 'renamed'
        assert documents[0].last_update == date.today()

    def test_rename_not_existing_document(self, changes, content, db):
        with pytest.raises(exceptions.ItemNotFound):
            content.rename(changes['renamed'])

    def test_rename_document_with_missing_handler(self, content):
        previous_path = PurePath('blog_articles/previous.html')
        new_path = PurePath('blog_articles/new.html')

        with pytest.raises(exceptions.HandlerNotFound):
            content.rename([(previous_path, new_path)])

    def test_rename_document_stored_in_another_directory(self, content):
        previous_path = PurePath('/invalid/previous.html')
        new_path = PurePath('/invalid/new.html')

        with pytest.raises(exceptions.InvalidDocumentLocation):
            content.rename([(previous_path, new_path)])

    @pytest.mark.skip("Only one category existing for now (blog articles)")
    def test_rename_document_with_new_category(self, content):
        raise NotImplementedError  # Should raise DocumentCategoryChanged

    # Delete documents.

    # TODO: Delete at least 2 documents of different kinds (02/2019)
    # Because that's how the content manager is intended to behave...
    def test_delete_documents(self, changes, content, db):
        article = ArticleFactory(uri='to_delete')
        content.delete(changes['deleted'])
        assert article.exists() is False

    def test_delete_not_existing_document(self, changes, content, db):
        with pytest.raises(exceptions.ItemNotFound):
            content.delete(changes['deleted'])

    def test_delete_document_with_missing_handler(self, content):
        source = PurePath('blog_articles/article.html')

        with pytest.raises(exceptions.HandlerNotFound):
            content.delete([source])

    def test_delete_document_stored_in_another_directory(self, content):
        source = PurePath('/invalid/article.html')

        with pytest.raises(exceptions.InvalidDocumentLocation):
            content.delete([source])

    # Get handler.

    def test_get_handler(self, content):
        source = content.directory / 'blog/2019/article.html'
        handler = content.get_handler(source)
        assert handler.__class__ is content.handlers['blog']

    def test_get_handler_with_relative_path(self, content):
        source = PurePath('blog/article.html')
        handler = content.get_handler(source)
        assert handler.__class__ is content.handlers['blog']

    def test_get_missing_handler(self, content):
        source = content.directory / 'reviews/article.html'

        with pytest.raises(exceptions.HandlerNotFound):
            content.get_handler(source)

    def test_document_not_stored_in_content_directory(self, content):
        source = PurePath('/void/article.html')

        with pytest.raises(exceptions.InvalidDocumentLocation):
            content.get_handler(source)

    def test_document_not_categorized(self, content):
        source = content.directory / 'article.html'

        with pytest.raises(exceptions.DocumentNotCategorized):
            content.get_handler(source)

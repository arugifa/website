"""Entry point to manage all content of my website.

Mainly base classes to be inherited by website's components.
"""

import asyncio
import logging
from io import StringIO
from pathlib import Path, PurePath
from typing import Callable, Dict, Iterable, List, Mapping, Tuple, Union

import aiofiles
from flask import render_template

from website import exceptions
from website.base.handlers import BaseDocumentFileHandler
from website.base.models import BaseDocument
from website.base.update import BaseUpdateManager, BaseUpdateRunner
from website.exceptions import DatabaseError, InvalidSourceFile
from website.utils.git import GitRepository

logger = logging.getLogger(__name__)


class ContentUpdateRunner(BaseUpdateRunner):

    @property
    def preview(self) -> str:
        # template = 'updates/content/preview.txt'
        # return render_template(template, changes=changes)
        output = StringIO()

        for action, files in self.todo:
            if files:
                print(f"The following files have been {action}:", file=output)

                for f in files:
                    if isinstance(f, tuple):
                        # - src_file -> dst_file
                        print("- ", end="", file=output)
                        print(*f, sep=" -> ", file=output)
                    else:
                        print(f"- {f}", file=output)

        return output.getvalue()

    @property
    def report(self):
        template = 'updates/content/report.txt'
        return render_template(template, result=result, errors=errors)

    async def _plan(self) -> Dict:
        errors = set()

        try:
            plan = self.manager.repository.diff(self.commit)
        except GitError as exc:
            errors.add(exc)

        return plan, errors

    async def _run(self) -> Tuple[Dict, Set]:
        """
        :raise website.exceptions.ItemAlreadyExisting:
            when trying to create documents already existing in database.
        :raise website.exceptions.ItemNotFound:
            when trying to modify documents not existing in database.
        :raise website.exceptions.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.
        """
        result = {}
        errors = set()

        def do(func):
            action = func.__name__ + 'ed'  # E.g., added, replaced, renamed, deleted
            result[action], error_set = await func(self.commit)
            errors = errors | error_set

        try:
            do(self.manager.repository.add)
            do(self.manager.repository.replace)
            do(self.manager.repository.rename)
            do(self.manager.repository.delete)
        except GitError as exc:
            errors.add(exc)

        return result, errors


class ContentManager:
    """Manage website's content life cycle.

    The content is organized as a set of categorized documents. For example::

        blog/
            2019/
                01-31. first_article_of_the_year.adoc
                12-31. last_article_of_the_year.adoc

    As part of website's content update, every document is loaded, processed,
    and finally stored, updated or deleted in the database.

    :param repository:
        path of the Git repository where website's content is stored.
    :param reader:
        function to read (and convert on the fly) documents.
    """

    def __init__(
            self, repository: GitRepository,
            handlers: Mapping[str, BaseDocumentFileHandler]):

        self.repository = repository
        self.handlers = handlers

    # Main API

    def load_changes(self, *, since: str) -> ContentUpdateRunner:
        # Get new DB session.
        try:
            yield ContentUpdateRunner(self, commit=since)
        except UpdateFailed:
            db.session.rollback()
            raise
        else:
            db.session.commit()

    # Helpers

    # TODO: Update docstring (03/2019)
    async def add(self, *, since: str) -> List[BaseDocument]:
        """Manually insert specific new documents into database.

        :param new:
            paths of documents source files.

        :raise website.exceptions.ItemAlreadyExisting:
            if a document already exists in database.
        :raise website.exceptions.HandlerNotFound:
            if a document doesn't have any handler defined in :attr:`handlers`.
        :raise website.exceptions.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.

        :return:
            newly created documents.
        """
        errors = set()
        to_add = self.repository.diff(commit)['added']  # Can raise GitError

        async def add(src):
            try:
                await self.get_handler(src).insert()
            except (DatabaseError, HandlerNotFound, InvalidSourceFile) as exc:
                errors.add(exc)
            return src

        return await asyncio.gather(add(src) for src in to_add), errors

    # TODO: Update docstring (03/2019)
    async def replace(self, *, since: str) -> List[BaseDocument]:
        """Manually update specific existing documents in database.

        :param existing:
            paths of documents source files.

        :raise website.exceptions.ItemNotFound:
            if a document doesn't exist in database.
        :raise website.exceptions.HandlerNotFound:
            if a document doesn't have any handler defined in :attr:`handlers`.
        :raise website.exceptions.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.

        :return:
            updated documents.
        """
        errors = set()
        to_replace = self.repository.diff(commit)['modified']  # Can raise GitError

        async def replace(src):
            try:
                await self.get_handler(src).update()
            except (DatabaseError, HandlerNotFound, InvalidSourceFile) as exc:
                errors.add(exc)
            return src

        return await asyncio.gather(replace(src) for src in to_replace)

    # TODO: Update docstring (03/2019)
    async def rename(self, *, since: str) -> List[BaseDocument]:
        """Manually rename and update specific existing documents in database.

        :param existing:
            previous and new paths of documents source files.

        :raise website.exceptions.ItemNotFound:
            if a document doesn't exist in database.
        :raise website.exceptions.HandlerNotFound:
            if a document doesn't have any handler defined in :attr:`handlers`.
        :raise website.exceptions.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.

        :return:
            updated documents.
        """
        errors = set()
        to_rename = self.repository.diff(commit)['renamed']  # Can raise GitError

        async def rename(src, dst):
            try:
                src_handler = self.get_handler(src)
                dst_handler = self.get_handler(dst)
            except HandlerNotFound as exc:
                errors.add(exc)
                return

            try:
                assert src_handler.__class__ is dst_handler.__class__
            except AssertionError:
                errors.add(exceptions.DocumentCategoryChanged(src, dst))
                return

            try:
                await src_handler.rename(dst)
            except (DatabaseError, InvalidSourceFile) as exc:
                errors.add(exc)
            return src, dst

        return await asyncio.gather(rename(src, dst) for src, dst in to_rename)

    def delete(self, *, since: str) -> None:
        """Manually delete specific documents from database.

        :param removed:
            paths of deleted documents source files.

        :raise website.exceptions.ItemNotFound:
            if a document doesn't exist in database.
        :raise website.exceptions.HandlerNotFound:
            if a document doesn't have any handler defined in :attr:`handlers`.
        :raise website.exceptions.InvalidDocumentLocation:
            when a source file is stored in a wrong directory.
        """
        errors = set()
        to_delete = self.repository.diff(commit)['deleted']  # Can raise GitError

        def delete(src):
            for src in to_delete:
                try:
                    self.get_handler(src).delete()
                except (DatabaseError, HandlerNotFound, InvalidSourceFile) as exc:
                    errors.add(exc)
                return src

        return [delete(src) for src in to_delete], errors

    # Helpers

    def get_handler(self, document: Union[Path, PurePath]) -> BaseDocumentFileHandler:
        """Return handler to process the source file of a document.

        :param document:
            path of the document's source file.

        :raise website.exceptions.HandlerNotFound:
            if no handler in :attr:`handlers` is defined
            for this type of document.
        :raise website.exceptions.InvalidDocumentLocation:
            when the source file is not located in :attr:`directory`
            or inside a subdirectory.
        """
        if document.is_absolute():
            try:
                relative_path = document.relative_to(self.repository.path)
            except ValueError:
                raise exceptions.InvalidDocumentLocation(document)
        else:
            relative_path = document

        try:
            category = list(relative_path.parents)[::-1][1].name
            handler = self.handlers[category]
        except IndexError:
            raise exceptions.DocumentNotCategorized(document)
        except KeyError:
            raise exceptions.HandlerNotFound(document)

        return handler(document, self.reader)

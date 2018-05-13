import logging
from datetime import date

from website import db

logger = logging.getLogger(__name__)


# Public API

def insert_documents(paths, callbacks, reader=open, prompt=input):
    """Add documents into the database."""
    for path in paths:
        try:
            insert = get_document_callback(path, callbacks)
        except KeyError:
            logger.error("No callback defined for inserting %s", path)
            raise

        content = reader(path).read()
        document = insert(path, content, prompt)
        db.session.add(document)


def delete_documents(paths, callbacks):
    """Delete documents from the database."""
    for path in paths:
        try:
            delete = get_document_callback(path, callbacks)
        except KeyError:
            logger.error("No callback defined for deleting %s", path)
            raise

        delete(path)


def rename_documents(paths, callbacks, reader=open, prompt=input):
    """Rename documents inside the database."""
    for src, dst in paths:
        try:
            assert src.parent == dst.parent
        except AssertionError:
            print(
                f"Cannot move {src.name} from {src.parent} to {dst.parent}: "
                "it should stay in the same top-level directory")
            raise

        try:
            rename = get_document_callback(dst, callbacks)
        except KeyError:
            logger.error("No callback defined for renaming %s", src)
            raise

        content = reader(dst).read()
        rename(dst, content, prompt)


def update_documents(paths, callbacks, reader=open, prompt=input):
    """Update documents inside the database."""
    for path in paths:
        try:
            update = get_document_callback(path, callbacks)
        except KeyError:
            logger.error("No callback defined for updating %s", path)
            raise

        content = reader(path).read()
        update(path, content, prompt)


# Helpers

def get_document_callback(path, callbacks):
    """Return callback function to process a document.

    :raise KeyError: when no callback is found.
    """
    document_type = get_document_type(path)
    return callbacks[document_type]


def get_document_date(path):
    """Return a document's date, based on the document's path.

    :param pathlib.Path path: document's path, relative to its repository.
    :raise ValueError: if document's path doesn't contain a proper date.
    """
    # Document's path:
    # <YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>
    try:
        year = int(path.parents[0].name)
        month, day = map(int, path.name.split('.')[0].split('-'))
    except (IndexError, TypeError, ValueError):
        error = 'Path "%s" does not contain a proper date'
        logger.exception(error, path)
        raise ValueError(error % path)

    return date(year, month, day)


def get_document_type(path):
    """Return a document's type, based on the document's path.

    :param pathlib.Path path: document's path, relative to its repository.
    :raise ValueError: if document is not stored in a directory.
    """
    # Document's path:
    # <TYPE>/<URI>.<EXTENSION>
    # <TYPE>/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>
    try:
        return list(path.parents)[-2].name
    except IndexError:
        error = 'Document "%s" must be classified in a directory'
        logger.exception(error, path)
        raise ValueError(error % path)


def get_document_uri(path):
    """Return a document's URI, based on the document's path.

    :param path: document's path, relative to its repository.
    :type path: Path
    """
    # Document's name:
    # <URI>.<EXTENSION>
    # <MONTH>-<DAY>.<URI>.<EXTENSION>
    return path.stem.split('.')[-1]

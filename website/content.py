import logging
from datetime import date
from pathlib import PurePath

from website import db
from website.exceptions import UpdateContentException

logger = logging.getLogger(__name__)


# Public API

def insert_documents(paths, callbacks, reader=open, prompt=input):
    """Add documents into the database."""
    for path in paths:
        callback = _get_callback('insert', path, callbacks)
        content = _read(path, reader)
        document = _do('insert', callback, path, content, prompt)
        db.session.add(document)


def delete_documents(paths, callbacks):
    """Delete documents from the database."""
    for path in paths:
        callback = _get_callback('delete', path, callbacks)
        _do('delete', callback, path)


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

        callback = _get_callback('rename', src, callbacks)
        content = _read(dst, reader)
        _do('rename', callback, dst, content, prompt)


def update_documents(paths, callbacks, reader=open, prompt=input):
    """Update documents inside the database."""
    for path in paths:
        callback = _get_callback('update', path, callbacks)
        content = _read(path, reader)
        _do('update', callback, path, content, prompt)


# Helpers

def get_document_callback(path, callbacks):
    """Return callback function to process a document.

    :param pathlib.Path path: document's path, relative to its repository.
    :raise KeyError: when no callback is found.
    :raise ValueError: if unable to get document's category type from its path.
    """
    # Document's path:
    # <TYPE>/<URI>.<EXTENSION>
    # <TYPE>/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>
    try:
        category = get_document_category(path)  # ValueError
        return callbacks[category]  # KeyError
    except (KeyError, ValueError):
        error = "No callback defined for %s"
        logger.error(error, path)
        raise KeyError(error % path)


def get_document_category(path):
    """Return a document's type, based on the document's path.

    :param pathlib.Path path: document's path, relative to its repository.
    :raise ValueError: if document is not stored in a directory.
    """
    # Document's path:
    # <TYPE>/<URI>.<EXTENSION>
    # <TYPE>/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>
    path = PurePath(path)

    try:
        return list(path.parents)[-2].name
    except IndexError:
        error = 'Document "%s" must be classified in a directory'
        logger.exception(error, path)
        raise ValueError(error % path)


def get_document_date(path):
    """Return a document's date, based on the document's path.

    :param pathlib.Path path: document's path, relative to its repository.
    :raise ValueError: if document's path doesn't contain a proper date.
    """
    # Document's path:
    # <YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>
    path = PurePath(path)

    try:
        year = int(path.parents[0].name)
        month, day = map(int, path.name.split('.')[0].split('-'))
    except (IndexError, TypeError, ValueError):
        error = 'Path "%s" does not contain a proper date'
        logger.error(error, path)
        raise ValueError(error % path)

    return date(year, month, day)


def get_document_uri(path):
    """Return a document's URI, based on the document's path.

    :param path: document's path, relative to its repository.
    :type path: Path
    """
    # Document's name:
    # <URI>.<EXTENSION>
    # <MONTH>-<DAY>.<URI>.<EXTENSION>
    path = PurePath(path)
    return path.stem.split('.')[-1]


# Private API

def _get_callback(action, path, callbacks):
    try:
        return get_document_callback(path, callbacks)
    except (KeyError, ValueError):
        error = f"Cannot find callback for %s"
        logger.error(error, path)
        raise UpdateContentException(error % path)


def _read(path, reader):
    try:
        return reader(path).read()
    except (OSError, UnicodeDecodeError) as exc:
        error = "Unable to read %s: %s"
        logger.error(error, path, exc)
        raise UpdateContentException(error % (path, exc))


def _do(action, callback, path, *args):
    try:
        return callback(path, *args)
    except Exception as exc:
        error = f"Failed to {action} %s: %s"
        logger.error(error, path, exc)
        raise UpdateContentException(error % (path, exc))

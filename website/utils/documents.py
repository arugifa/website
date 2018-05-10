import logging
from datetime import date

from website import db

logger = logging.getLogger(__name__)


# Documents Editing

def insert_documents(paths, callbacks, reader=open, prompt=input):
    """Add documents into the database."""
    for path in paths:
        document_type = retrieve_document_type(path)
        content = reader(path).read()

        try:
            create = callbacks[document_type]
        except KeyError:
            logger.error(
                'Cannot insert "%s" into database: '
                'no callback defined for "%s"',
                path, document_type)

        document = create(path, content, prompt)
        db.session.add(document)


def delete_documents(paths, callbacks):
    """Delete documents from the database."""

    for path in paths:
        document_type = retrieve_document_type(path)

        try:
            delete = callbacks[document_type]
        except KeyError:
            logger.error(
                'Cannot remove "%s" from database: '
                'no callback defined for "%s"',
                path, document_type)

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

        document_type = retrieve_document_type(dst)
        content = reader(dst).read()

        try:
            rename = callbacks[document_type]
        except KeyError:
            logger.error(
                'Cannot update "%s" into database: '
                'no callback defined for "%s"',
                paths[1], document_type)

        rename(dst, content, prompt)


def update_documents(paths, callbacks, reader=open, prompt=input):
    """Update documents inside the database."""
    for path in paths:
        document_type = retrieve_document_type(path)
        content = reader(path).read()

        try:
            update = callbacks[document_type]
        except KeyError:
            logger.error(
                'Cannot update "%s" into database: '
                'no callback defined for "%s"',
                path, document_type)

        update(path, content, prompt)


# Document Processing

"""
def load_document(path):
    document_type = retrieve_document_type(path)
    model = CONTENT_DIRECTORIES[document_type]
    uri = retrieve_document_uri(path)
    return model.find(uri=uri)
"""


def retrieve_document_date(path):
    """Return a document's date, based on the document's path.

    :param path: document's path, relative to its repository.
    :type path: Path
    """
    # Document's path:
    # <TYPE>/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>
    year = int(path.parents[0].name)
    month, day = map(int, path.name.split('.')[0].split('-'))
    return date(year, month, day)


def retrieve_document_type(path):
    """Return a document's type, based on the document's path.

    :param path: document's path, relative to its repository.
    :type path: Path
    """
    # Document's path:
    # <TYPE>/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>
    return list(path.parents)[-2].name


def retrieve_document_uri(path):
    """Return a document's URI, based on the document's path.

    :param path: document's path, relative to its repository.
    :type path: Path
    """
    # Document's name:
    # <MONTH>-<DAY>.<URI>.<EXTENSION>
    return path.name.split('.')[1]

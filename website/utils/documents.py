import logging
from datetime import date

logger = logging.getLogger(__name__)


# Documents Editing

def add_documents(files, db, callbacks, reader=open):
    """Add documents into the database.

    Should be called from inside a Flask application's context.
    """
    for path in files:
        document_type = retrieve_document_type(path)
        content = reader(path).read()

        try:
            create = callbacks[document_type]
        except KeyError:
            logger.error(
                'No callback defined to add "%s" documents',
                document_type)

        document = create(path, content)
        db.session.add(document)


def delete_documents(files, db):
    """Delete documents from the database.

    Should be called from inside a Flask application's context.
    """
    for path in files:
        document = load_document(path)
        db.session.delete(document)


def rename_documents(files, reader=open):
    """Rename documents inside the database.

    Should be called from inside a Flask application's context.
    """
    for paths in files:
        src = paths[0].parents[0]
        dst = paths[1].parents[0]

        try:
            assert src == dst
        except AssertionError:
            name = paths[0].name
            print(
                f"Cannot move {name} from {src} to {dst}: "
                "it should stay in the same top-level directory")
            raise

        document = load_document(paths[0])
        document_type = retrieve_document_type(path)
        content = reader(paths[1]).read()

        update = CONTENT_REPOSITORY[document_type]['update']
        update(document, paths[1], content)


def update_documents(files, reader=open):
    """Update documents inside the database.

    Should be called from inside a Flask application's context.
    """
    for path in files:
        document = load_document(path)
        document_type = retrieve_document_type(path)
        content = reader(path).read()

        update = CONTENT_REPOSITORY[document_type]['update']
        update(document, path, content)


# Document Processing

def load_document(path):
    """Load a document from the database.

    Should be called from inside a Flask application's context.
    """
    document_type = retrieve_document_type(path)
    model = CONTENT_DIRECTORIES[document_type]
    uri = retrieve_document_uri(path)
    return model.find(uri=uri)


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

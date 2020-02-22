"""All high-level exceptions raised inside my website."""


class WebsiteException(Exception):
    """Base exception for all project's exceptions."""


# Database Exceptions

class DatabaseError(WebsiteException):
    """Errors related to the database."""


# TODO: Rename to DatabaseLookupError? (02/2020)
class ItemNotFound(DatabaseError):
    """If a lookup in database for a specific item doesn't return any result."""


class MultipleItemsFound(DatabaseError):
    """Raised if several results are returned when looking for a specific item."""


class InvalidItem(DatabaseError):
    """If trying to save in database an item which presents integrity errors."""


class ItemAlreadyExisting(DatabaseError):
    """If trying to insert in database an item already existing."""


# Content Exceptions

class DocumentLoadingError(WebsiteException):
    """Error happening when loading (i.e., reading and parsing) a document's source file."""  # noqa: E501


class DocumentParsingError(WebsiteException):
    """When errors raise while parsing a document."""


class DocumentMalformatted(DocumentParsingError):
    """When syntax errors are found while parsing a document."""


class DocumentTitleMissing(DocumentParsingError):
    """When the title of a document is not found in its source file."""


class DocumentCategoryMissing(DocumentParsingError):
    """When the category of a document is not found in its source file."""


class DocumentProcessingError(WebsiteException):
    pass


class DocumentPathScanningError(DocumentProcessingError):
    pass


class DocumentCategoryNotFound(DocumentProcessingError):
    pass


class DocumentTagsNotFound(DocumentProcessingError):
    pass


class InvalidFile(WebsiteException):
    pass


# Update Exceptions

class UpdateError(WebsiteException):
    pass


class UpdateAborted(UpdateError):
    """When the user cancels an update."""


class UpdateFailed(UpdateError):
    pass

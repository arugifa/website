"""All high-level exceptions raised inside my website."""


class WebsiteException(Exception):
    """Base exception for all project's exceptions."""


# Database Exceptions

class DatabaseException(WebsiteException):
    """Errors related to the database."""


class ItemNotFound(DatabaseException):
    """If a lookup in database for a specific item doesn't return any result."""


class MultipleItemsFound(DatabaseException):
    """Raised if several results are returned when looking for a specific item."""


class InvalidItem(DatabaseException):
    """If trying to save in database an item which presents integrity errors."""


class ItemAlreadyExisting(DatabaseException):
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


class ArticleDateMalformatted(DocumentParsingError):
    """When syntax errors are found while parsing the date of an article."""


class ArticleCategoryMissing(DocumentParsingError):
    """When the category of an article is not found in its source file."""


class ArticleLeadMissing(DocumentParsingError):
    """When the lead paragraph of an article is not found in its source file."""


class ArticleLeadMalformatted(DocumentParsingError):
    """When syntax errors are found while parsing the lead paragraph of an article."""


class ArticleBodyMissing(DocumentParsingError):
    """When the body of an article is not found in its source file."""

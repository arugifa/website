"""All high-level exceptions raised inside my website."""


class WebsiteException(Exception):
    """Base exception for all project's exceptions."""


# Database Exceptions

class DatabaseException(WebsiteException):
    """Errors related to the database."""


class MultipleItemsFound(DatabaseException):
    """Raised if several results are returned when looking for a specific item."""  # noqa: E501


class ItemNotFound(DatabaseException):
    pass


class ItemAlreadyExisting(DatabaseException):
    pass


# Content Exceptions

class DocumentError(WebsiteException):
    pass


class DocumentParsingError(DocumentError):
    pass


class ArticleCategoryMissing(DocumentParsingError):
    pass


class ArticleTitleMissing(DocumentParsingError):
    pass


class ArticleLeadMissing(DocumentParsingError):
    pass


class ArticleLeadMalformatted(DocumentParsingError):
    pass


class ArticleBodyMissing(DocumentParsingError):
    pass


class DocumentLoadingError(WebsiteException):
    pass


class ContentUpdateException(WebsiteException):
    pass

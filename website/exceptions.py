"""All high-level exceptions raised inside my website."""


class WebsiteException(Exception):
    """Base exception for all project's exceptions."""


# Database Exceptions

class DatabaseException(WebsiteException):
    """Errors related to the database."""


class MultipleResultsFound(WebsiteException):
    """Raised if several results are returned when looking for a specific item."""  # noqa: E501


# Content Exceptions

class DocumentError(WebsiteException):
    pass


class DocumentLoadingError(WebsiteException):
    pass

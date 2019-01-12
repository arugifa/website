class WebsiteException(Exception):
    """Base exception for all other exceptions."""


# Database Exceptions

class DatabaseException(WebsiteException):
    """Errors related to the database."""


class MultipleResultsFound(WebsiteException):
    """Raised if several results are returned when looking for a specific item."""  # noqa: E501


# Content Exceptions

class UpdateContentException(WebsiteException):
    """Raised if an error happens when loading website's content into database."""  # noqa: E501

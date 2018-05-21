class WebsiteException(Exception):
    pass


# Database Exceptions

class DatabaseException(WebsiteException):
    pass


class MultipleResultsFound(DatabaseException):
    pass


# Content Exceptions

class UpdateContentException(WebsiteException):
    pass

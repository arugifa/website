class WebsiteException(Exception):
    pass


# Database Related Exceptions

class DatabaseException(WebsiteException):
    pass


class MultipleResultsFound(WebsiteException):
    pass

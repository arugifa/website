"""All high-level exceptions raised inside my website."""

from arugifa.cms import exceptions as cms_errors


class WebsiteException(Exception):
    """Base exception for all project's exceptions."""


# Database Exceptions

# TODO: Rename to DatabaseLookupError? (02/2020)
class ItemNotFound(cms_errors.DatabaseError):
    """If a lookup in database for a specific item doesn't return any result."""


class MultipleItemsFound(cms_errors.DatabaseError):
    """Raised if several results are returned when looking for a specific item."""


class InvalidItem(cms_errors.DatabaseError):
    """If trying to save in database an item which presents integrity errors."""


# TODO: Replace ItemAlreadyExisting with:
class DupplicatedContent(cms_errors.DatabaseError):
    """If trying to insert in database item(s) already existing."""


# Content Exceptions

class DocumentMalformatted(cms_errors.SourceParsingError):
    """When syntax errors are found while parsing a document."""


class DocumentTitleMissing(cms_errors.SourceParsingError):
    """When the title of a document is not found in its source file."""


class DocumentCategoryMissing(cms_errors.SourceParsingError):
    """When the category of a document is not found in its source file."""


class DocumentCategoryNotFound(cms_errors.FileProcessingError):
    pass


class DocumentTagsNotFound(cms_errors.FileProcessingError):
    def __str__(self):
        # TODO: Handler singular/plurial (05/2020)
        tags = ', '.join(self.args[0])
        return f"Tags not found: {tags}"


class InvalidCategoryNames(cms_errors.SourceParsingError):
    pass


class InvalidTagNames(cms_errors.SourceParsingError):
    pass


class BlankCategories(cms_errors.SourceParsingError):
    pass

"""Exceptions specific to the blog section."""

from website.exceptions import DocumentParsingError, DocumentPathScanningError


class ArticleInvalidLocation(DocumentPathScanningError):
    pass


class ArticleDateMalformatted(DocumentPathScanningError):
    """When syntax errors are found while parsing the date of an article."""


class ArticleLeadMissing(DocumentParsingError):
    """When the lead paragraph of an article is not found in its source file."""


class ArticleLeadMalformatted(DocumentParsingError):
    """When syntax errors are found while parsing the lead paragraph of an article."""


class ArticleBodyMissing(DocumentParsingError):
    """When the body of an article is not found in its source file."""

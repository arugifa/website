"""Exceptions specific to the blog section."""

from arugifa.cms import exceptions as cms_errors


class ArticleInvalidLocation(cms_errors.FilePathScanningError):
    pass


class ArticleDateMalformatted(cms_errors.FilePathScanningError):
    """When syntax errors are found while parsing the date of an article."""


class ArticleLeadMissing(cms_errors.SourceParsingError):
    """When the lead paragraph of an article is not found in its source file."""


class ArticleLeadMalformatted(cms_errors.SourceParsingError):
    """When syntax errors are found while parsing the lead paragraph of an article."""


class ArticleBodyMissing(cms_errors.SourceParsingError):
    """When the body of an article is not found in its source file."""

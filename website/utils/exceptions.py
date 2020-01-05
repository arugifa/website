"""Exceptions related to CLI tools we use."""

from website.exceptions import WebsiteException


class RepositoryNotFound(WebsiteException):
    """If a directory doesn't contain any Git repository."""

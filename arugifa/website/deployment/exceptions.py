"""Exceptions related to online deployment."""

from arugifa.website.exceptions import WebsiteException


class CloudError(WebsiteException):
    """Base Cloud exception."""


class CloudConnectionFailure(CloudError):
    """Couldn't connect to the Cloud."""


class CloudContainerNotFound(CloudError):
    """Object container not found online."""


class CloudUploadError(CloudError):
    """Couldn't upload a file."""


class CloudFileNotFound(CloudError):
    """Couldn't retrieve a file online."""
    pass

"""Anything related to Cloud connection and management."""

from typing import Callable

import openstack
from openstack.exceptions import SDKException

from arugifa.website.deployment import exceptions
from arugifa.website.deployment.typing import CloudConnection


def connect(factory: Callable = openstack.connect) -> CloudConnection:
    """Connect to an OpenStack based Cloud.

    :param factory:
        function used for connection.
    :return:
        the connection itself.
    :raise website.exceptions.CloudConnectionFailure:
        if something wrong happens.
    """
    try:
        return factory()
    except SDKException as exc:
        raise exceptions.CloudConnectionFailure(exc)

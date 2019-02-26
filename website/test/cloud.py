from typing import Callable, List, Union

from openstack.connection import Connection
from openstack.object_store.v1.container import Container

from website.stubs import (
    CloudStubConnection, CloudStubConnectionFactory, CloudStubContainer)

# To not clash with PROD containers.
TEST_CONTAINERS_PREFIX = 'test'


class CloudTestClient:
    """Helper to connect to the Cloud during tests.

    Use by default :class:`website.stubs.CloudConnectionStub` for connections.

    This behavior can be changed at any time by resetting a Cloud object
    (with :meth:`~.reset`), and giving a different connection class.
    """

    def __init__(self):
        self.reset()

    def reset(self, factory: Callable = CloudStubConnectionFactory) -> Union[
            Connection, CloudStubConnection]:
        self.connection = factory()

    def clean(self) -> List[Union[Container, CloudStubContainer]]:
        containers = [
            c for c in self.connection.object_store.containers()
            if c.name.startswith(TEST_CONTAINERS_PREFIX)
        ]

        for container in containers:
            objects = list(self.connection.object_store.objects(container))

            for obj in objects:
                self.connection.object_store.delete_object(obj)

            self.connection.object_store.delete_container(container)

        return containers

"""Helpers to be used when writing tests."""

from contextlib import contextmanager
from typing import Callable

import openstack
import openstack.exceptions

from website.deployment.stubs import CloudStubConnection
from website.deployment.typing import CloudConnection, CloudContainers
from website.test.stubs import stub

# To not clash with PROD containers.
TEST_CONTAINERS_PREFIX = 'test'


class CloudStubConnectionFactory:
    """Create stub connections for unit tests."""

    def __init__(self, network: object = None):
        self.network = network or FakeNetwork()

    @stub(openstack.connect, classified=True)
    def __call__(  # noqa: D102
            self, cloud=None, app_name=None, app_version=None, options=None,
            load_yaml_config=True, load_envvars=True, **kwargs):
        if self.network.disconnected:
            raise openstack.exceptions.SDKException(
                "A network outage has been manually triggered")

        connection = CloudStubConnection()
        connection._network = self.network
        return connection


class CloudTestClient:
    """Client to be used when connecting to an OpenStack Cloud during test.

    Client can be reset at any time, e.g., to use a different connection between tests::

        import openstack.connect
        from openstack.connection import Connection
        from website.deployment.stubs import CloudStubConnectionFactory

        client = CloudTestClient(openstack.connect)
        run_integration_test(client)

        client.reset(CloudStubConnectionFactory)
        run_unit_test(client)
    """

    def __init__(self, factory: Callable = CloudStubConnectionFactory):
        self.reset(factory)

    def reset(self, factory: Callable = CloudStubConnectionFactory) -> CloudConnection:
        """Reset underlying connection."""
        self.connection = factory()

    def clean(self) -> CloudContainers:
        """Remove containers (and objects inside) created during test.

        :return: deleted containers.
        """
        containers = [
            c for c in self.connection.object_store.containers()
            if c.name.startswith(TEST_CONTAINERS_PREFIX)
        ]

        for container in containers:
            objects = list(self.connection.object_store.objects(container))

            for obj in objects:
                self.connection.object_store.delete_object(obj)

            # From time to time, cleanup fails for some strange reason:
            #
            #   openstack.exceptions.ConflictException: ConflictException: 409:
            #   Client Error for url: https://<CLOUD>/v1/<TOKEN>/test_container_<XX>,
            #   ConflictThere was a conflict when trying to complete your request.
            #
            # Trying to delete the container a second time works most of the time.
            # OpenStack probably needs some time to reflect changes performed on
            # containers.
            #
            try:
                self.connection.object_store.delete_container(container)
            except openstack.exceptions.ConflictException:
                try:
                    self.connection.object_store.delete_container(container)
                except openstack.exceptions.ResourceNotFound:
                    continue

        return containers


class FakeNetwork:
    """Simulate network perturbations during test."""

    def __init__(self):
        self.disconnected = False

    @contextmanager
    def unplug(self):
        """Simulate a network outage.

        Can be used as follows::

            def my_test():
                network = FakeNetwork()
                client = Client(network)

                with network.unplug(), pytest.raises(NetworkError):
                    client.download_files()
        """
        self.disconnected = True

        try:
            yield
        finally:
            self.disconnected = False

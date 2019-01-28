from typing import Callable, List

from website.stubs import CloudConnectionStub

# To not clash with PROD containers.
TEST_CONTAINER_PREFIX = 'test'


class CloudTestClient:
    """Helper to connect to the Cloud during tests.

    Use by default :class:`website.stubs.CloudConnectionStub` for connections.

    This behavior can be changed at any time by resetting a Cloud object
    (with :meth:`~.reset`), and giving a different connection class.
    """

    def __init__(self):
        self.connection = None
        self.reset('test_user', 'api_key', 'mars')

    def reset(self, username, api_key, region, cls=CloudConnectionStub):
        #self.connection = utils.connect_to_the_cloud(
        #    username, api_key, region, cls)
        pass

    def clean(self):
        containers = filter(
            lambda c: c.name.startswith(TEST_CONTAINER_PREFIX),
            self.connection.object_store.containers())

        for container in containers:
            # XXX: list(objects) ??
            objects = self.connection.object_store.objects(container)

            for obj in objects:
                self.connection.object_store.delete_object(obj)

            self.connection.object_store.delete_container(container)

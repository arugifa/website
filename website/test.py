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
        self.connection = utils.connect_to_the_cloud(
            username, api_key, region, cls)

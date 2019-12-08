import pytest

from website.deployment import cloud
from website.deployment import exceptions
from website.deployment.stubs import CloudStubConnection
from website.deployment.test import CloudStubConnectionFactory


class TestConnect:
    def test_cloud_connection(self):
        factory = CloudStubConnectionFactory()
        connection = cloud.connect(factory)
        assert isinstance(connection, CloudStubConnection)

    def test_error_happening_during_connection(self, network):
        factory = CloudStubConnectionFactory(network)

        with network.unplug(), pytest.raises(exceptions.CloudConnectionFailure):  # noqa: E501
            cloud.connect(factory)

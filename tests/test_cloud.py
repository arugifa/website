from openstack.exceptions import NotFoundException
import pytest

from website.cloud import TEST_CONTAINER_PREFIX
from website.cloud.factories import ContainerFactory, ObjectFactory
from website.cloud.helpers import retrieve_test_containers
from website.cloud.stubs import ConnectionStub


class TestObjectStore:

    # Containers

    def test_create_container(self, cloud):
        name = f'{TEST_CONTAINER_PREFIX}_container'
        container = cloud.object_store.create_container(name=name)
        assert container.name == 'test_container'

    def test_create_container_without_test_prefix(self, cloud):
        if not isinstance(cloud, ConnectionStub):
            pytest.skip("Only apply to stub connection")

        with pytest.raises(AssertionError):
            cloud.object_store.create_container(name='prod')

    def test_delete_container(self, cloud):
        container = ContainerFactory()
        cloud.object_store.delete_container(container)

        with pytest.raises(NotFoundException):
            cloud.object_store.get_container_metadata(container)

    def test_get_container_metadata(self, cloud):
        expected = ContainerFactory()
        actual = cloud.object_store.get_container_metadata(expected)
        assert actual.name == expected.name

    def test_get_unexisting_container_metadata(self, cloud):
        container = f'{TEST_CONTAINER_PREFIX}_container'

        with pytest.raises(NotFoundException):
            actual = cloud.object_store.get_container_metadata(container)

    def test_retrieve_containers(self, cloud):
        expected_containers = ContainerFactory.create_batch(2)
        actual_containers = retrieve_test_containers(cloud)

        assert len(actual_containers) == len(expected_containers)

        for actual, expected in zip(actual_containers, expected_containers):
            assert actual.name == expected.name

    # Objects

    def test_delete_object(self, cloud):
        container = ContainerFactory()
        obj = ObjectFactory(container=container.name)

        cloud.object_store.delete_object(obj)
        actual_objects = list(cloud.object_store.objects(container))

        assert len(actual_objects) == 0

    def test_get_object(self, cloud):
        expected_data = b'Test Data'
        obj = ObjectFactory(data=expected_data)

        actual_data = cloud.object_store.get_object(obj)
        assert actual_data == expected_data

    def test_get_object_metadata(self, cloud):
        expected = ObjectFactory()
        actual = cloud.object_store.get_object_metadata(expected)

        assert actual.container == expected.container
        assert actual.name == expected.name

    def test_retrieve_objects(self, cloud):
        container = ContainerFactory()

        actual_objects = ObjectFactory.create_batch(2, container=container)
        expected_objects = list(cloud.object_store.objects(container))

        assert len(actual_objects) == len(expected_objects)

        for actual, expected in zip(actual_objects, expected_objects):
            assert actual.name == expected.name

    def test_upload_object(self, cloud):
        # Fixtures
        container = ContainerFactory()

        expected_data = b'Test Data'
        expected_object = ObjectFactory.build(
            container=container.name, data=expected_data)

        # Tests
        actual_object = cloud.object_store.upload_object(
            container=expected_object.container, name=expected_object.name,
            data=expected_data)

        actual_data = cloud.object_store.get_object(actual_object)

        # Assertions
        assert actual_object.container == expected_object.container
        assert actual_object.name == expected_object.name
        assert actual_data == expected_data


class TestObject:
    def test_etag(self, cloud):
        data = b'Test Data'
        md5_hash = 'f315202b28422ed5c2af4f843b8c2764'

        obj = ObjectFactory(data=data)
        assert obj.etag == md5_hash

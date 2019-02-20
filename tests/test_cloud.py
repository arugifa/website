from openstack.exceptions import NotFoundException
import pytest

from website.test.cloud import TEST_CONTAINERS_PREFIX
from website.factories import ContainerFactory, ObjectFactory


class TestObjectStore:

    # Containers

    def test_create_container(self, cloud):
        container = ContainerFactory(name='container')
        assert container.name == f'{TEST_CONTAINERS_PREFIX}_container'

    def test_delete_container(self, cloud):
        container = ContainerFactory()
        cloud.object_store.delete_container(container)

        with pytest.raises(NotFoundException):
            cloud.object_store.get_container_metadata(container)

    def test_get_container(self, cloud):
        expected = ContainerFactory()
        actual = cloud.object_store.get_container_metadata(expected)
        assert actual.name == expected.name

    def test_get_not_existing_container(self, cloud):
        container = f'{TEST_CONTAINERS_PREFIX}_missing'

        with pytest.raises(NotFoundException):
            cloud.object_store.get_container_metadata(container)

    def test_retrieve_containers(self, cloud):
        expected_containers = ContainerFactory.create_batch(2)
        actual_containers = [
            c for c in cloud.object_store.containers()
            if c.name.startswith(TEST_CONTAINERS_PREFIX)
        ]
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
        expected = ObjectFactory()
        actual = cloud.object_store.get_object(expected)

        assert actual.container == expected.container
        assert actual.name == expected.name
        assert actual.data == expected.data

    def test_get_object_metadata(self, cloud):
        expected = ObjectFactory()
        actual = cloud.object_store.get_object_metadata(expected)

        assert actual.container == expected.container
        assert actual.name == expected.name
        assert actual.data == expected.data

    def test_retrieve_objects(self, cloud):
        container = ContainerFactory()

        actual_objects = sorted(
            ObjectFactory.create_batch(2, container=container),
            key=lambda o: o.name,
        )
        expected_objects = sorted(
            cloud.object_store.objects(container),
            key=lambda o: o.name,
        )
        assert len(actual_objects) == len(expected_objects)

        for actual, expected in zip(actual_objects, expected_objects):
            assert actual.name == expected.name

    def test_upload_object(self, cloud):
        container = ContainerFactory(name='uploads')

        obj = cloud.object_store.upload_object(
            container, 'uploaded', data=b'Uploaded object')

        assert obj.container == container.name
        assert obj.name == 'uploaded'
        assert obj.data == b'Uploaded object'


class TestObject:
    def test_etag(self, cloud):
        data = b'Test Data'
        md5_hash = 'f315202b28422ed5c2af4f843b8c2764'

        obj = ObjectFactory(data=data)
        assert obj.etag == md5_hash

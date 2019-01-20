from hashlib import md5

from openstack.exceptions import NotFoundException


class CloudConnectionStub:
    def __init__(self, username, api_key, region):
        self.object_store = CloudObjectStoreStub()

        # TODO: test raise SDKException


class CloudObjectStoreStub:
    def __init__(self):
        self._containers = dict()

    # Containers

    def containers(self):
        yield from self._containers.values()

    def create_container(self, **attrs):
        name = attrs['name']

        error = "Don't mess up with PROD data!"
        assert name.startswith('test'), error

        container = CloudContainerStub(attrs)
        self._containers[name] = container
        return container

    def delete_container(self, container):
        name = getattr(container, 'name', container)
        del self._containers[name]

    def get_container_metadata(self, container):
        name = getattr(container, 'name', container)

        try:
            return self._containers[name]
        except KeyError:
            raise NotFoundException

    # Objects

    def delete_object(self, obj):
        object_name = getattr(obj, 'name', obj)
        del self._containers[obj.container]._objects[object_name]

    def get_object(self, obj):
        object_name = getattr(obj, 'name', obj)
        container_name = obj.container

        obj = self._containers[container_name]._objects[object_name]
        return obj._data

    def get_object_metadata(self, obj, container=None):
        if container is None:
            container_name = obj.container
        else:
            container_name = getattr(container, 'name', container)

        object_name = getattr(obj, 'name', obj)
        return self._containers[container_name]._objects[object_name]

    def objects(self, container):
        name = getattr(container, 'name', container)
        yield from self._containers[name]._objects.values()

    def upload_object(self, **attrs):
        container_name = getattr(
            attrs['container'], 'name', attrs['container'])
        container = self._containers[container_name]

        object_name = attrs['name']
        object_attributes = {
            'container': container_name,
            'data': attrs['data'],
            'name': object_name,
        }

        obj = CloudObjectStub(object_attributes)
        container._objects[object_name] = obj
        return obj


class CloudContainerStub:
    def __init__(self, attrs):
        self._objects = dict()
        self.name = attrs['name']


class CloudObjectStub:
    def __init__(self, attrs):
        self._data = attrs['data']
        self.container = attrs['container']
        self.name = attrs['name']

    @property
    def etag(self):
        return md5(self._data).hexdigest()

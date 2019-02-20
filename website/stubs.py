from hashlib import md5

from openstack.exceptions import NotFoundException


def cloud_stub_factory():
    return CloudStubConnection()


class CloudStubConnection:
    def __init__(self):
        self.object_store = CloudStubObjectStore()

        # TODO: test raise SDKException


class CloudStubObjectStore:
    def __init__(self):
        self._containers = dict()

    # Containers

    def containers(self):
        yield from self._containers.values()

    def create_container(self, name, **attrs):
        container = CloudStubContainer(name=name, **attrs)
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

    def delete_object(self, obj, container=None):
        container = container or obj.container
        name = getattr(obj, 'name', obj)
        del self._containers[container]._objects[name]

    def get_object(self, obj, container=None):
        container = container or obj.container
        name = getattr(obj, 'name', obj)
        return self._containers[container]._objects[name]

    def get_object_metadata(self, obj, container=None):
        container = container or obj.container
        name = getattr(obj, 'name', obj)
        return self._containers[container]._objects[name]

    def objects(self, container):
        name = getattr(container, 'name', container)
        yield from self._containers[name]._objects.values()

    def upload_object(self, container, name, **attrs):
        container_name = getattr(container, 'name', container)
        container = self._containers[container_name]

        obj = CloudStubObject(
            container=container_name,
            name=name,
            data=attrs['data'],
        )
        container._objects[name] = obj
        return obj


class CloudStubContainer:
    def __init__(self, **attrs):
        self._objects = dict()
        self.name = attrs['name']


class CloudStubObject:
    def __init__(self, data=None, **attrs):
        self.container = attrs['container']
        self.name = attrs['name']
        self.data = data

    @property
    def etag(self):
        return md5(self.data).hexdigest()

"""...

https://docs.openstack.org/openstacksdk/latest/user/proxies/object_store.html
"""
from copy import copy
from hashlib import md5
from inspect import getmembers, isclass, isfunction, signature

import openstack
from openstack.connection import Connection
from openstack.exceptions import NotFoundException
from openstack.object_store.v1._proxy import Proxy as ObjectStore
from openstack.object_store.v1.container import Container
from openstack.object_store.v1.obj import Object


def fqin(obj):
    """Return the Fully Qualified Import Name of an object."""
    return f'{obj.__module__}.{obj.__qualname__}'


def stub(original):
    """Check that stub signatures are up-to-date.

    The main purpose is to avoid bugs to sneak in the codebase. This can
    happen:

    - if keyword arguments are used in interface tests when checking stub
      behaviors,
    - but positional arguments are used everywhere else in the codebase.

    In this case, if the signature of function/methods tested changes (e.g.,
    when upgrading their library), then the interface tests would remain GREEN,
    but the codebase would miserably crashes when shipped into production.
    """
    def wrapper(obj):
        try:
            if isfunction(obj):
                original_fqin = fqin(original)
                stub_fqin = fqin(obj)

                original_signature = signature(original)
                stub_signature = signature(obj)

                assert stub_signature == original_signature

            elif isclass(obj):
                methods = getmembers(obj, isfunction)

                for name, stub_method in methods:
                    original_method = getattr(original, name)

                    if not original_method:
                        continue

                    original_fqin = fqin(original_method)
                    stub_fqin = fqin(stub_method)

                    original_signature = signature(original_method)
                    stub_signature = signature(stub_method)

                    assert stub_signature == original_signature

        except AssertionError:
            error = (
                f'Signature of {stub_fqin} differs from {original_fqin}: '
                f'{stub_signature} != {original_signature}'
            )
            raise ValueError(error)

        return obj

    return wrapper


@stub(openstack.connect)
def cloud_stub_factory(
        cloud=None, app_name=None, app_version=None, options=None,
        load_yaml_config=True, load_envvars=True, **kwargs):
    return CloudStubConnection()


@stub(Connection)
class CloudStubConnection:
    def __init__(
            self, cloud=None, config=None, session=None, app_name=None,
            app_version=None, extra_services=None, strict=False,
            use_direct_get=False, task_manager=None, rate_limit=None, **kwargs):  # noqa: E501
        self.object_store = CloudStubObjectStore()

        # TODO: test raise SDKException


@stub(ObjectStore)
class CloudStubObjectStore:
    def __init__(self, *args, **kwargs):
        self._containers = dict()

    # Containers

    def containers(self, **query):
        yield from self._containers.values()

    def create_container(self, name, **attrs):
        container = CloudStubContainer(name=name, **attrs)
        self._containers[name] = container
        return container

    def get_container_metadata(self, container):
        name = getattr(container, 'name', container)

        try:
            return self._containers[name]
        except KeyError:
            raise NotFoundException

    def delete_container(self, container, ignore_missing=True):
        name = getattr(container, 'name', container)
        del self._containers[name]

    # Objects

    def objects(self, container, **query):
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

    def get_object(self, obj, container=None):
        if isinstance(obj, CloudStubObject):
            return self._containers[obj.container]._objects[obj.name]

        metadata = copy(self._containers[container]._objects[obj])
        metadata.name = None
        metadata.data = None

        return metadata

    def get_object_metadata(self, obj, container=None):
        return self.get_object(obj, container)

    def delete_object(self, obj, ignore_missing=True, container=None):
        container = container or obj.container
        name = getattr(obj, 'name', obj)
        del self._containers[container]._objects[name]


@stub(Container)
class CloudStubContainer:
    def __init__(self, _synchronized=False, connection=None, **attrs):
        self._objects = dict()
        self.name = attrs['name']


@stub(Object)
class CloudStubObject:
    def __init__(self, data=None, **attrs):
        self.id = attrs['name']

        self.container = attrs['container']
        self.name = attrs['name']
        self.data = data

    @property
    def etag(self):
        return md5(self.data).hexdigest()

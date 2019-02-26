"""...

https://docs.openstack.org/openstacksdk/latest/user/proxies/object_store.html
"""
from contextlib import contextmanager
from copy import copy
from hashlib import md5
from inspect import getmembers, isclass, isfunction, signature

import openstack
from openstack.connection import Connection
from openstack.exceptions import (
    InvalidRequest, NotFoundException, ResourceNotFound, SDKException)
from openstack.object_store.v1._proxy import Proxy as ObjectStore
from openstack.object_store.v1.container import Container
from openstack.object_store.v1.obj import Object


def fqin(obj):
    """Return the Fully Qualified Import Name of an object."""
    return f'{obj.__module__}.{obj.__qualname__}'


def stub(original, classified=False):
    """Check that stub signatures are up-to-date.

    The main purpose is to avoid bugs to sneak in the codebase. This can
    happen:

    - if keyword arguments are used in interface tests when checking stub
      behaviors,
    - but positional arguments are used everywhere else in the codebase.

    In this case, if the signature of function/methods tested changes (e.g.,
    when upgrading their library), then the interface tests would remain GREEN,
    but the codebase would miserably crashes when shipped into production.

    :param classified:
        set to ``True`` when using an instance method to make a function stub.
        This will remove the ``self`` attribute from the stub signature,
        so both the stub method and the original function have the same
        signature. Using methods is useful to generate side effects on the fly,
        depending on the stub instance attributes.
    """
    def wrapper(obj):
        try:
            if isfunction(obj):
                original_fqin = fqin(original)
                stub_fqin = fqin(obj)

                original_signature = signature(original)
                stub_signature = signature(obj)

                if classified:
                    original_parameters = filter(
                        lambda p: p.name != 'self',
                        signature(obj).parameters.values(),
                    )
                    stub_signature = stub_signature.replace(
                        parameters=original_parameters)

                assert stub_signature == original_signature

            elif isclass(obj):
                def is_method(attr):
                    return isfunction(attr) and attr.__name__ in original.__dict__  # noqa: E501

                methods = getmembers(obj, is_method)

                for name, stub_method in methods:
                    original_method = getattr(original, name)

                    original_fqin = fqin(original_method)
                    stub_fqin = fqin(stub_method)

                    original_signature = signature(original_method)
                    stub_signature = signature(stub_method)

                    assert stub_signature == original_signature

            else:
                error = f"{stub_fqin} should be either a class or a function"
                raise TypeError(error)

        except AssertionError:
            error = (
                f'Signature of {stub_fqin} differs from {original_fqin}: '
                f'{stub_signature} != {original_signature}'
            )
            raise ValueError(error)

        return obj

    return wrapper


class NetworkStub:
    def __init__(self):
        self.disconnected = False

    @contextmanager
    def unplug(self):
        """Simulate a network outage to generate exceptions during tests.

        For example::

            with network.unplug(), pytest.raises(SDKException):
                object_store.create_container('test_container')
        """
        self.disconnected = True

        try:
            yield
        finally:
            self.disconnected = False


class CloudStubConnectionFactory:
    def __init__(self, network=None):
        self.network = network or NetworkStub()

    @stub(openstack.connect, classified=True)
    def __call__(
            self, cloud=None, app_name=None, app_version=None, options=None,
            load_yaml_config=True, load_envvars=True, **kwargs):
        if self.network.disconnected:
            raise SDKException("A network outage has been manually triggered")

        connection = CloudStubConnection()
        connection._network = self.network
        return connection


@stub(Connection)
class CloudStubConnection:
    def __init__(
            self, cloud=None, config=None, session=None, app_name=None,
            app_version=None, extra_services=None, strict=False,
            use_direct_get=False, task_manager=None, rate_limit=None, **kwargs):  # noqa: E501
        # Original attributes.
        self.object_store = CloudStubObjectStore(_connection=self)

        # Stub Attributes.
        self._network = None  # Must be manually assigned after instantiation

    # Stub Methods

    def execute(self, method):
        """Method decorator to change cloud's behavior on the fly during tests.

        For example::

            connection.execute(object_store.create_container)('test_container')

        Used by :meth:`CloudStubResource.__getattribute__`.
        """
        if self._network.disconnected:
            raise SDKException("Network has been manually unplugged")

        return method


class CloudStubResource:
    """Base class for cloud resources using :class:`CloudStubConnection`."""

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)

        if callable(attr):
            return self._connection.execute(attr)

        return attr


@stub(ObjectStore)
class CloudStubObjectStore(CloudStubResource):
    def __init__(self, *args, **kwargs):
        # Original attributes.
        self._connection = kwargs['_connection']

        # Stub attributes.
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

        if name is None:
            raise InvalidRequest("Request requires an ID but none was found")

        obj = CloudStubObject(
            container=container_name,
            name=name,
            data=attrs['data'],
        )
        self._containers[container_name]._objects[name] = obj

        return obj

    def download_object(self, obj, container=None, **attrs):
        if isinstance(obj, CloudStubObject):
            return self._containers[obj.container]._objects[obj.name]._data

        container_name = getattr(container, 'name', container)

        try:
            return self._containers[container_name]._objects[obj]._data
        except KeyError:
            raise ResourceNotFound("404: Client Error")

    def get_object(self, obj, container=None):
        if isinstance(obj, CloudStubObject):
            return self._containers[obj.container]._objects[obj.name]

        try:
            metadata = copy(self._containers[container]._objects[obj])
        except KeyError:
            raise NotFoundException

        metadata.name = None
        metadata.data = None

        return metadata

    def get_object_metadata(self, obj, container=None):
        return self.get_object(obj, container)

    def delete_object(self, obj, ignore_missing=True, container=None):
        try:
            if isinstance(obj, CloudStubObject):
                del self._containers[obj.container]._objects[obj.name]

            else:
                container_name = getattr(container, 'name', container)
                del self._containers[container_name]._objects[obj]

        except KeyError:
            raise ResourceNotFound


@stub(Container)
class CloudStubContainer:
    def __init__(self, _synchronized=False, connection=None, **attrs):
        # Original attributes.
        self.connection = connection
        self.name = attrs['name']

        # Stub attributes.
        self._objects = dict()


@stub(Object)
class CloudStubObject:
    def __init__(self, data=None, **attrs):
        self.id = attrs['name']

        self.container = attrs['container']
        self.name = attrs['name']
        self.data = self._data = data

    @property
    def etag(self):
        return md5(self._data).hexdigest()

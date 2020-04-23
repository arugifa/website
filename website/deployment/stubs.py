"""OpenStack stubs, to be used inside unit tests.

OpenStack's official API:
https://docs.openstack.org/openstacksdk/latest/user/proxies/object_store.html
"""

from copy import copy
from datetime import datetime
from hashlib import md5

from openstack.connection import Connection
from openstack.exceptions import (
    InvalidRequest, NotFoundException, ResourceNotFound, SDKException)
from openstack.object_store.v1._proxy import Proxy as ObjectStore
from openstack.object_store.v1.container import Container
from openstack.object_store.v1.obj import Object

from website.test.stubs import stub


@stub(Connection)
class CloudStubConnection:
    """Simulate connection to an OpenStack Cloud.

    To be used like that::

        from website.deployment.test import FakeNetwork

        connection = CloudStubConnection()
        connection._network = FakeNetwork()
    """

    def __init__(
            self, cloud=None, config=None, session=None, app_name=None,
            app_version=None, extra_services=None, strict=False,
            use_direct_get=False, task_manager=None, rate_limit=None,
            oslo_conf=None, service_types=None, global_request_id=None,
            strict_proxies=False, **kwargs):

        self.object_store = CloudStubObjectStore(_connection=self)

        # To simulate network perturbations, when manipulating containers or objects.
        # Must be manually assigned after instantiation.
        self._network = None

    def execute(self, method):  # noqa: D401
        """Method decorator to change cloud's behavior on the fly during tests.

        For example::

            connection.execute(object_store.create_container)('test_container')

        Used by :meth:`.CloudStubResource.__getattribute__`.

        :raise openstack.exceptions.SDKException:
            when simulated network problems happen.
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
    """Represent an object store on an OpenStack Cloud."""

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

    def upload_object(
            self, container, name, filename=None, md5=None, sha256=None,
            segment_size=None, use_slo=True, metadata=None,
            generate_checksums=None, data=None, **headers):
        container_name = getattr(container, 'name', container)

        if name is None:
            raise InvalidRequest("Request requires an ID but none was found")

        obj = CloudStubObject(container=container_name, name=name, data=data)
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
    """Represent a container on an OpenStack Cloud."""

    def __init__(self, _synchronized=False, connection=None, **attrs):
        # Original attributes.
        self.connection = connection
        self.name = attrs['name']

        # Stub attributes.
        self._objects = dict()


@stub(Object)
class CloudStubObject:
    """Represent an object on an OpenStack cloud."""

    def __init__(self, data=None, **attrs):
        self.id = attrs['name']

        self.container = attrs['container']
        self.name = attrs['name']
        self.data = self._data = data
        self.last_modified_at = datetime.now().isoformat()

    @property
    def etag(self):
        return md5(self._data).hexdigest()

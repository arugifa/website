"""Collection of Cloud factories to create dynamic fixtures during test."""

from factory import Factory, SelfAttribute, Sequence, SubFactory
from factory.base import FactoryOptions, OptionDefault
from openstack.object_store.v1.container import Container
from openstack.object_store.v1.obj import Object

from website.deployment.test import CloudTestClient, TEST_CONTAINERS_PREFIX


# Base Classes

class _CloudFactoryOptions(FactoryOptions):
    """Allow to configure a Cloud testing client in sub-factories."""

    def _build_default_options(self):
        default_options = super()._build_default_options()
        cloud_client = [OptionDefault('cloud', None, inherit=True)]
        return default_options + cloud_client


class _BaseCloudFactory(Factory):
    """Pointless base factory with custom options related to Cloud connection.

    This class is absolutely needed, as we cannot set directly ``Meta`` options and
    ``_options_class`` variable at the same time on :class:`.BaseCloudFactory`. Doing so
    is raising an exception at runtime::

        TypeError: 'class Meta' for <class 'BaseCloudFactory'> got unknown attribute(s) cloud
    """  # noqa: E501

    _options_class = _CloudFactoryOptions

    class Meta:
        abstract = True


class BaseCloudFactory(_BaseCloudFactory):
    """Actual base factory for all Cloud related factories."""

    _options_class = _CloudFactoryOptions

    class Meta:
        abstract = True
        cloud = CloudTestClient()


# Actual Factories

class ContainerFactory(BaseCloudFactory):
    """Create object containers.

    Add prefix to created containers, to prevent deleting already existing containers
    during tests cleanup. This can happen when running tests on a production environment
    (e.g., because it's not possible to set-up an isolated testing environment).
    """

    class Meta:
        model = Container

    name = Sequence(lambda n: f'container_{n}')

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        kwargs['name'] = f"{TEST_CONTAINERS_PREFIX}_{kwargs['name']}"
        return super()._build(model_class, *args, **kwargs)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        cloud = cls._meta.cloud.connection
        kwargs['name'] = f"{TEST_CONTAINERS_PREFIX}_{kwargs['name']}"
        return cloud.object_store.create_container(**kwargs)


class ObjectFactory(BaseCloudFactory):
    """Create objects."""

    class Meta:
        model = Object
        exclude = ['_container']

    _container = SubFactory(ContainerFactory)
    container = SelfAttribute('_container.name')
    data = b'Test Data'
    name = Sequence(lambda n: 'test_object_%d.txt' % n)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        cloud = cls._meta.cloud.connection
        return cloud.object_store.upload_object(**kwargs)

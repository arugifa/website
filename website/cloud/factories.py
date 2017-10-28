from abc import abstractmethod

from factory import Factory, Sequence, SubFactory, lazy_attribute
from factory.base import FactoryOptions, OptionDefault
from openstack.object_store.v1.container import Container
from openstack.object_store.v1.obj import Object

from . import TEST_CONTAINERS_PREFIX, utils
from .stubs import ConnectionStub


class Cloud:
    """Helper to connect to the Cloud during tests.

    Use by default :class:`.ConnectionStub` for connections.

    This behavior can be changed at any time by resetting a Cloud object
    (with :meth:`~.reset`), and giving a different connection class.
    """

    def __init__(self):
        self.connection = None
        self.reset('test_user', 'api_key', 'mars')

    def reset(self, username, api_key, region, cls=ConnectionStub):
        self.connection = utils.connect_to_the_cloud(
            username, api_key, region, cls)


class CloudFactoryOptions(FactoryOptions):
    def _build_default_options(self):
        default_options = super()._build_default_options()
        cloud_options = [OptionDefault('cloud', None, inherit=True)]
        return default_options + cloud_options


class _BaseCloudFactory(Factory):
    _options_class = CloudFactoryOptions

    class Meta:
        abstract = True


class BaseCloudFactory(_BaseCloudFactory):
    class Meta:
        abstract = True
        cloud = Cloud()

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        return model_class(kwargs)

    @classmethod
    @abstractmethod
    def _create(cls, model_class, *args, **kwargs):
        pass


class ContainerFactory(BaseCloudFactory):
    class Meta:
        model = Container

    name = Sequence(lambda n: f'{TEST_CONTAINERS_PREFIX}_container_%d' % n)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        cloud = cls._meta.cloud.connection
        return cloud.object_store.create_container(**kwargs)


class ObjectFactory(BaseCloudFactory):
    class Meta:
        model = Object

    container = None  # Defined in _build() and _create()
    data = b'Test Data'
    name = Sequence(lambda n: 'test_object_%d.txt' % n)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        container = kwargs.get('container') or ContainerFactory.build().name
        kwargs['container'] = container
        return super()._build(model_class, *args, **kwargs)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        cloud = cls._meta.cloud.connection

        # Had to make a workaround, because strangely, this returns None:
        # kwargs.pop('container', ContainerFactory.create())
        # However, if executing the same statement in PDB, alles gut!...
        container = kwargs.pop('container', None) or ContainerFactory.create()

        return cloud.object_store.upload_object(container=container, **kwargs)

# TODO: Update docstring
"""Base classes to be inherited from by factories all over the website."""

from factory import Factory, SelfAttribute, Sequence, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from factory.base import FactoryOptions, OptionDefault
from openstack.object_store.v1.container import Container
from openstack.object_store.v1.obj import Object

from website import db
from website.test.cloud import CloudTestClient, TEST_CONTAINERS_PREFIX


# Database
# ========

class BaseDatabaseFactory(SQLAlchemyModelFactory):
    """Base factory for every model."""

    class Meta:
        abstract = True
        sqlalchemy_session = db.session

        # Database session is committed after fixtures creation.
        # So we don't have to do it manually, when playing around
        # in a Flask shell for example...
        sqlalchemy_session_persistence = 'commit'


# Cloud
# =====

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
        cloud = CloudTestClient()


class ContainerFactory(BaseCloudFactory):
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

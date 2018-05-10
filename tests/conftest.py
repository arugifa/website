import pytest
import webtest
from rackspace.connection import Connection

from website import db as _db
from website.cloud.factories import BaseCloudFactory
from website.cloud.helpers import retrieve_test_containers
from website.cloud.stubs import ConnectionStub
from website.config import TestingConfig
from website.helpers import create_app
from website.test.integration import CommandLine, InvokeStub
from website.test.pytest import FixtureMarker

integration_test = FixtureMarker()


# Pytest Configuration

def pytest_addoption(parser):
    parser.addoption('--cloud_username')
    parser.addoption('--cloud_api_key')
    parser.addoption('--cloud_region')


def pytest_generate_tests(metafunc):
    if 'cloud' in metafunc.fixturenames:
        if metafunc.module.__name__ == 'test_cloud':
            params = [ConnectionStub, Connection]
        else:
            params = [ConnectionStub]

        metafunc.parametrize('cloud_connection', params, indirect=True)


def pytest_collection_modifyitems(items):
    global integration_test

    for item in items:
        if 'tests/acceptance/' in item.module.__file__:
            item.add_marker(pytest.mark.acceptance)
        elif integration_test.fixtures & set(item.fixturenames):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


# Fixtures

@pytest.fixture(scope='session')
def app():
    # Used by pytest-flask.
    return create_app(TestingConfig)


@pytest.fixture
def client(app):
    # Overwrite client fixture from pytest-flask
    # to use Webtest instead of Flask default test client.
    return webtest.TestApp(app)


@pytest.fixture(scope='module')
@integration_test
def cloud_connection(request):
    username = request.config.getoption('cloud_username')
    api_key = request.config.getoption('cloud_api_key')
    region = request.config.getoption('cloud_region')
    config = [username, api_key, region]

    if not all(config) and request.param is Connection:
        return pytest.skip("Cloud connection not configured")

    cloud = BaseCloudFactory._meta.cloud
    cloud.reset(username, api_key, region, cls=request.param)

    return cloud.connection


@pytest.fixture
@integration_test
def cloud(cloud_connection):
    yield cloud_connection

    test_containers = retrieve_test_containers(cloud_connection)

    for container in test_containers:
        objects = list(cloud_connection.object_store.objects(container))

        for obj in objects:
            cloud_connection.object_store.delete_object(obj)

        cloud_connection.object_store.delete_container(container)


@pytest.fixture
def db(app):
    # Create and drop all tables for every test,
    # as transaction support with SQLAlchemy + SQLite is clumsy.
    # Didn't find a way yet to make it work.

    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope='session')
@integration_test
def invoke():
    return CommandLine('invoke')


@pytest.fixture(scope='session')
@integration_test
def invoke_ctx():
    return InvokeStub()

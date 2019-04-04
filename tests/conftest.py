import inspect
import re
import shlex
from pathlib import Path
from subprocess import PIPE, run

import openstack
import pytest
pytest.register_assert_rewrite('website.test.integration')
import webtest

from website import create_app, db as _db
from website.cloud import CloudFilesManager
from website.config import TestingConfig
from website.factories import BaseCloudFactory
from website.stubs import CloudStubConnectionFactory, NetworkStub
from website.test.integration import (
    CommandLine, FileFixtureCollection, InvokeStub, TestingPrompt, RunReal,
    RunStub, TestingShell)
from website.test.pytest import FixtureMarker
from website.utils.asciidoctor import AsciidoctorToHTMLConverter
from website.utils.git import Repository

here = Path(__file__).parent.resolve()
integration_test = FixtureMarker()


# Pytest Configuration

def pytest_generate_tests(metafunc):
    if 'cloud' in metafunc.fixturenames:
        if metafunc.module.__name__ == 'test_stubs':
            params = ['stub', 'original']
        else:
            params = ['stub']

        metafunc.parametrize('cloud_client', params, indirect=True)


def pytest_collection_modifyitems(items):
    global integration_test

    for item in items:
        # Apply markers to identify acceptance, integration and unit tests.
        integration_fixtures = integration_test.fixtures & set(item.fixturenames)  # noqa: E501

        if 'tests/acceptance/' in item.module.__file__:
            item.add_marker(pytest.mark.acceptance)

        elif integration_fixtures:
            item.add_marker(pytest.mark.integration)

            for fixture in integration_fixtures:
                marker = getattr(pytest.mark, fixture)
                item.add_marker(marker)

        else:
            item.add_marker(pytest.mark.unit)

        # Apply marker to identify async tests.
        if inspect.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# Fixtures

@pytest.fixture(scope='session')
def app():
    # Used by pytest-flask.
    return create_app(TestingConfig)


@pytest.fixture(scope='session')
@integration_test
def asciidoctor():
    asciidoctor = AsciidoctorToHTMLConverter()
    assert asciidoctor.is_installed()
    return asciidoctor


@pytest.fixture
def client(app):
    # Overwrite client fixture from pytest-flask
    # to use Webtest instead of Flask default test client.
    return webtest.TestApp(app)


@pytest.fixture
@integration_test
def cloud_client(network, request):
    if request.param == 'stub':
        connection_factory = CloudStubConnectionFactory(network)
    elif request.param == 'original':
        connection_factory = openstack.connect
    else:
        raise ValueError(request.param)

    client = BaseCloudFactory._meta.cloud
    client.reset(factory=connection_factory)
    return client


@pytest.fixture
@integration_test
def cloud(cloud_client):
    yield cloud_client.connection
    cloud_client.clean()


@pytest.fixture
def network():
    return NetworkStub()


@pytest.fixture
def object_store(cloud):
    cloud.object_store.create_container('test_files')
    return CloudFilesManager(cloud, 'test_files')


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


@pytest.fixture(scope='session')
def fixtures(request, tmp_path_factory):
    directory = here / '_fixtures'
    symlinks = tmp_path_factory.mktemp('fixtures')
    return FileFixtureCollection(directory, request, symlinks)


@pytest.fixture(scope='session')
@integration_test
def git():
    git = Repository
    # assert git.is_installed()
    return git


@pytest.fixture
def prompt():
    return TestingPrompt()


@pytest.fixture
def shell():
    return TestingShell()


@pytest.fixture(scope='session')
@integration_test
def shell_bck():
    def runner(cmdline):
        cmdline = shlex.split(cmdline)
        return run(cmdline, check=True, stdout=PIPE, encoding='utf-8')

    return runner


# Fixes

# TODO: Update pytest-splinter when issue #112 is fixed (01/2019)
# See https://github.com/pytest-dev/pytest-splinter/issues/112
# When not using this patch, Pytest fails with:
#   Fixture "tmpdir" called directly. Fixtures are not meant to be called directly,
#   but are created automatically when test functions request them as parameters.

def _mk_tmp(request, factory):
    name = request.node.name
    name = re.sub(r"[\W]", "_", name)
    MAXVAL = 30
    name = name[:MAXVAL]
    return factory.mktemp(name, numbered=True)


@pytest.fixture(scope='session')
def session_tmpdir(request, tmpdir_factory):
    """pytest tmpdir which is session-scoped."""
    return _mk_tmp(request, tmpdir_factory)

import re
import shlex
from pathlib import Path
from subprocess import PIPE, run

import pytest
pytest.register_assert_rewrite('website.test.integration')
import webtest
from rackspace.connection import Connection

from website import create_app, db as _db
from website.config import TestingConfig
from website.factories import BaseCloudFactory
from website.stubs import CloudConnectionStub
from website.test.integration import (
    CommandLine, FileFixtureCollection, InvokeStub, Prompt, RunReal, RunStub,
    Shell)
from website.test.pytest import FixtureMarker
from website.utils.asciidoctor import AsciidoctorToHTMLConverter

here = Path(__file__).parent.resolve()
integration_test = FixtureMarker()


# Pytest Configuration

def pytest_addoption(parser):
    parser.addoption('--cloud_username')
    parser.addoption('--cloud_api_key')
    parser.addoption('--cloud_region')


def pytest_generate_tests(metafunc):
    if 'cloud' in metafunc.fixturenames:
        if metafunc.module.__name__ == 'test_cloud':
            params = [CloudConnectionStub, Connection]
        else:
            params = [CloudConnectionStub]

        metafunc.parametrize('cloud_connection', params, indirect=True)


def pytest_collection_modifyitems(items):
    global integration_test

    for item in items:
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


# Fixtures

@pytest.fixture(scope='session')
def app():
    # Used by pytest-flask.
    return create_app(TestingConfig)


@pytest.fixture(scope='session')
@integration_test
def asciidoctor():
    return AsciidoctorToHTMLConverter()


@pytest.fixture
def client(app):
    # Overwrite client fixture from pytest-flask
    # to use Webtest instead of Flask default test client.
    return webtest.TestApp(app)


@pytest.fixture(scope='module')
@integration_test
def cloud_client(request):
    username = request.config.getoption('cloud_username')
    api_key = request.config.getoption('cloud_api_key')
    region = request.config.getoption('cloud_region')
    config = [username, api_key, region]

    if not all(config) and request.param is Connection:
        return pytest.skip("Cloud connection not configured")

    cloud_client = BaseCloudFactory._meta.cloud
    cloud_client.reset(username, api_key, region, cls=request.param)

    return cloud_client


@pytest.fixture
@integration_test
def cloud(cloud_client):
    yield cloud_client
    cloud_client.clean()


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


@pytest.fixture(params=[RunStub, RunReal])
@integration_test
def git(request):
    return request.param()


@pytest.fixture
def prompt():
    return Prompt()


@pytest.fixture
def shell():
    return Shell()


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

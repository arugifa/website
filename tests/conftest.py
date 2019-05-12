import inspect
import re
from pathlib import Path

import pytest
pytest.register_assert_rewrite('website.test.integration')  # Rewrite helper assertions
import webtest

from website import create_app, db as _db
from website.config import TestingConfig
from website.test.integration import CommandLine, TestingPrompt, TestingShell
from website.test.local_fixtures import FileFixtureCollection
from website.test.pytest import FixtureMarker
from website.utils.asciidoctor import AsciidoctorToHTMLConverter

here = Path(__file__).parent.resolve()
integration_test = FixtureMarker()


# Pytest Configuration
# ====================

def pytest_collection_modifyitems(items):
    """Apply dynamic test markers."""
    global integration_test

    for item in items:
        # Apply markers to identify acceptance, integration and unit tests.
        integration_fixtures = integration_test.fixtures & set(item.fixturenames)

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
# ========

# General

@pytest.fixture(scope='session')
def fixtures(tmp_path_factory):
    """Look for fixtures stored in local files."""
    directory = here / '_fixtures'
    symlinks = tmp_path_factory.mktemp('fixtures')
    return FileFixtureCollection(directory, symlinks)


# Web Tests

@pytest.fixture(scope='session')
def app():
    """Return a Flask application."""
    # Used by pytest-flask.
    return create_app(TestingConfig)


@pytest.fixture
def client(app):
    """Return a WSGI test client for the Flask application."""
    # Overwrite client fixture from pytest-flask
    # to use Webtest instead of Flask default test client.
    return webtest.TestApp(app)


@pytest.fixture
def db(app):
    """Clean database between test executions."""
    # Create and drop all tables for every test,
    # as transaction support with SQLAlchemy + SQLite is clumsy.
    # Didn't find a way yet to make it work.

    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


# Integration Tests

@pytest.fixture  # Async fixtures can only be function-scoped
@integration_test
async def asciidoctor():
    """Check if Asciidoctor is installed when running tests."""
    asciidoctor = AsciidoctorToHTMLConverter()
    assert await asciidoctor.is_installed()
    return asciidoctor


@pytest.fixture(scope='session')
@integration_test
def invoke():
    """Execute commands with Invoke."""
    # XXX: Check if Invoke is installed? (05/2019)
    return CommandLine('invoke')


@pytest.fixture
def prompt():
    """Dependency to inject in the codebase when user input is needed."""
    return TestingPrompt()


@pytest.fixture(scope='session')
@integration_test
def sass():
    """Execute commands with Sass."""
    # XXX: Check if Sassc is installed? (05/2019)
    return CommandLine('sassc')


@pytest.fixture
def shell():
    """Dependency to inject in the codebase when external programs have to be executed."""  # noqa: E501
    return TestingShell()


# Fixes
# =====

# TODO: Update pytest-splinter when issue #112 is fixed (01/2019)
# See https://github.com/pytest-dev/pytest-splinter/issues/112
# When not using this patch, Pytest fails with:
#   Fixture "tmpdir" called directly. Fixtures are not meant to be called
#   directly, but are created automatically when test functions request them as
#   parameters.

def _mk_tmp(request, factory):
    name = request.node.name
    name = re.sub(r"[\W]", "_", name)
    MAXVAL = 30  # noqa: N806
    name = name[:MAXVAL]
    return factory.mktemp(name, numbered=True)


@pytest.fixture(scope='session')
def session_tmpdir(request, tmpdir_factory):  # noqa: D103
    return _mk_tmp(request, tmpdir_factory)

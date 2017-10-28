from pathlib import PurePath

import pytest
from pytest_bdd import when


# TODO: Find out why Pytest-BDD does not load this fixture
# before running tests. However, when the fixture is defined
# in the same module than the tests, everything is alright.
@pytest.fixture('session')
def pytestbdd_feature_base_dir():
    return PurePath(__file__).parent / 'features'


@pytest.fixture(scope='session')
def splinter_driver_kwargs():
    # Running tests with Firefox in headless mode is faster.
    return {'headless': True}


@pytest.fixture(scope='session')
def splinter_screenshot_dir():
    return str(PurePath(__file__).parent / 'screenshots')


# Gherkin Actions

@when("I access to my website")
def access_website(browser, live_server):
    browser.visit(live_server.url('/'))

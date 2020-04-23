import multiprocessing
import sys
from pathlib import PurePath

import pytest
from pytest_bdd import when

# XXX: See https://github.com/pytest-dev/pytest-flask/issues/104 (04/2020)
if sys.platform == 'darwin':
    multiprocessing.set_start_method('fork')


# TODO: Why Pytest-BDD doesn't load this fixture before running tests? (10/2017)
# However, when the fixture is defined in the same module than the tests,
# everything is alright.
@pytest.fixture('session')
def pytestbdd_feature_base_dir():
    """Don't look for features in the top-level testing directory."""
    return PurePath(__file__).parent / 'features'


@pytest.fixture(scope='session')
def splinter_driver_kwargs():
    """Run tests with Firefox in headless mode, for greater speed."""
    return {'headless': True}


@pytest.fixture(scope='session')
def splinter_screenshot_dir():
    """Don't store the screenshots in the current working directory."""
    return str(PurePath(__file__).parent / 'screenshots')


# Gherkin Actions

@when("I access to my website")
def access_website(browser, live_server):
    """Navigate to the website's homepage."""
    browser.visit(live_server.url('/'))

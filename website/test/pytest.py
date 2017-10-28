"""Test helpers to be used with Pytest."""

from typing import Callable, Iterable


class FixtureMarker:
    """Apply a marker to user-defined Pytest fixtures.

    Useful for example to mark some tests, using specific fixtures, as integration
    tests. For example::

        integration_test = ['database']

        @pytest.fixture
        @integration_test
        def web_client():
            ...

        def pytest_collection_modifyitems(items):
            global integration_test

            for item in items:
                if integration_test.fixtures & set(item.fixturenames):
                    item.add_marker(pytest.mark.integration)
                else:
                    item.add_marker(pytest.mark.unit)

        def test_something(database, web_client):  # Marked as integration test
            ...
    """

    def __init__(self, fixtures: Iterable = None):
        """Initialize the marker with an optional list of fixture names."""
        self.fixtures = set(fixtures) if fixtures else set()

    def __call__(self, fixture: Callable):
        """Mark additional fixtures, when the marker is used as a decorator."""
        self.fixtures.add(fixture.__name__)
        return fixture

from website import test


class TestFixtureMarker:
    def test_decorate_fixtures(self):
        integration_test = test.FixtureMarker()

        @integration_test
        def fixture_1():
            pass

        @integration_test
        def fixture_2():
            pass

        assert integration_test.fixtures == {'fixture_1', 'fixture_2'}

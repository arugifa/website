class FixtureMarker:
    def __init__(self, fixtures=None):
        self.fixtures = set(fixtures) if fixtures else set()

    def __call__(self, fixture):
        self.fixtures.add(fixture.__name__)
        return fixture

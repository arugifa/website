from pathlib import Path

from website import config
from website.helpers import create_app


class BaseTestConfig:
    config_class = None

    def test_can_define_new_keys(self):
        config = self.config_class(SOME_KEY='some_key', OTHER_KEY='other_key')
        assert config.SOME_KEY == 'some_key'
        assert config.OTHER_KEY == 'other_key'

    def test_can_overwritte_default_values(self, monkeypatch):
        monkeypatch.setattr(
            self.config_class, 'EXISTING_KEY', 'default_value', raising=False)

        assert self.config_class.EXISTING_KEY == 'default_value'
        config = self.config_class(EXISTING_KEY='new_value')
        assert config.EXISTING_KEY == 'new_value'


class TestDefaultConfig(BaseTestConfig):
    config_class = config.DefaultConfig


class TestDevelopmentConfig(BaseTestConfig):
    config_class = config.DevelopmentConfig

    def test_can_set_database_path(self, monkeypatch):
        monkeypatch.setenv('WEBSITE_DB', '/tmp/test.db')
        app = create_app(self.config_class())
        assert str(app.config['DATABASE_USER_PATH']) == '/tmp/test.db'

    def test_relative_database_path_is_made_absolute(self, monkeypatch):
        monkeypatch.setenv('WEBSITE_DB', 'test.db')
        app = create_app(self.config_class())

        expected = str(Path.cwd() / 'test.db')
        assert str(app.config['DATABASE_USER_PATH']) == expected


class TestTestingConfig(BaseTestConfig):
    config_class = config.TestingConfig

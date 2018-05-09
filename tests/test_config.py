from pathlib import Path, PurePath

from website import config


class BaseTestConfig:
    config_class = None

    def test_can_define_new_settings_at_runtime(self):
        config = self.config_class(
            SOME_SETTING='some_setting', OTHER_SETTING='other_setting')

        assert config.SOME_SETTING == 'some_setting'
        assert config.OTHER_SETTING == 'other_setting'

    def test_can_overwritte_default_settings(self, monkeypatch):
        monkeypatch.setattr(
            self.config_class,
            'DEFAULT_SETTING', 'default_value',
            raising=False,
        )
        assert self.config_class.DEFAULT_SETTING == 'default_value'

        config = self.config_class(DEFAULT_SETTING='new_value')
        assert config.DEFAULT_SETTING == 'new_value'


class TestDefaultConfig(BaseTestConfig):
    config_class = config.DefaultConfig


class TestDevelopmentConfig(BaseTestConfig):
    config_class = config.DevelopmentConfig

    def test_can_set_database_via_environment_variable(self, monkeypatch):
        monkeypatch.setenv('WEBSITE_DB', '/tmp/test.db')
        config = self.config_class()
        assert str(config.DATABASE_PATH) == '/tmp/test.db'

    def test_can_define_database_path_at_runtime(self):
        config = self.config_class(DATABASE_PATH='/tmp/test.db')
        assert str(config.DATABASE_PATH) == '/tmp/test.db'

    def test_runtime_value_for_database_overwrittes_environment_variable(
            self, monkeypatch):
        monkeypatch.setenv('WEBSITE_DB', '/tmp/test_env.db')
        config = self.config_class(DATABASE_PATH='/tmp/test_runtime.db')
        assert str(config.DATABASE_PATH) == '/tmp/test_runtime.db'

    def test_relative_database_path_is_made_absolute(self):
        config = self.config_class(DATABASE_PATH='test.db')
        expected = str(Path.cwd() / 'test.db')
        assert str(config.DATABASE_PATH) == expected

    def test_can_use_path_object_or_string_for_database_path(self):
        # Should not raise.
        self.config_class(DATABASE_PATH=PurePath('/tmp/test.db'))
        self.config_class(DATABASE_PATH='/tmp/test.db')


class TestTestingConfig(BaseTestConfig):
    config_class = config.TestingConfig

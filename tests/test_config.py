from pathlib import PurePath
from typing import ClassVar

import pytest

from arugifa.website import config


class BaseTestConfig:
    config_class: ClassVar[config.DefaultConfig] = None

    def test_can_overwritte_default_settings(self, monkeypatch):
        monkeypatch.setattr(
            self.config_class, 'DEFAULT_SETTING', 'default_value', raising=False,
        )
        assert self.config_class.DEFAULT_SETTING == 'default_value'

        config = self.config_class(DEFAULT_SETTING='new_value')
        assert config.DEFAULT_SETTING == 'new_value'

    def test_can_define_new_settings_at_runtime(self):
        config = self.config_class(
            SOME_SETTING='some_setting', OTHER_SETTING='other_setting')

        assert config.SOME_SETTING == 'some_setting'
        assert config.OTHER_SETTING == 'other_setting'


class TestDefaultConfig(BaseTestConfig):
    config_class = config.DefaultConfig


class TestDevelopmentConfig(BaseTestConfig):
    config_class = config.DevelopmentConfig

    @pytest.fixture
    def db_path(self, tmpdir):
        return PurePath(tmpdir.ensure('test.db'))

    # Database Path

    def test_can_set_database_path_with_an_environment_variable(
            self, db_path, monkeypatch):
        monkeypatch.setenv('WEBSITE_DB', str(db_path))
        config = self.config_class()

        assert config.DATABASE_PATH == db_path
        assert config.SQLALCHEMY_DATABASE_URI == f'sqlite:///{db_path}'

    def test_can_define_database_path_at_runtime(self, db_path):
        config = self.config_class(DATABASE_PATH=db_path)
        assert config.DATABASE_PATH == db_path
        assert config.SQLALCHEMY_DATABASE_URI == f'sqlite:///{db_path}'

    def test_runtime_value_for_database_path_overwrittes_environment_variable(
            self, db_path, monkeypatch):
        monkeypatch.setenv('WEBSITE_DB', '/tmp/test_env.db')
        config = self.config_class(DATABASE_PATH=db_path)
        assert config.DATABASE_PATH == db_path

    def test_relative_database_path_is_made_absolute(self, db_path, monkeypatch):
        db_file = db_path.name

        monkeypatch.chdir(db_path.parent)
        config = self.config_class(DATABASE_PATH=db_file)

        assert config.DATABASE_PATH == db_path

    def test_can_use_path_object_or_string_for_database_path(self, db_path):
        # Should not raise.
        self.config_class(DATABASE_PATH=db_path)
        self.config_class(DATABASE_PATH=str(db_path))

    def test_in_memory_database_is_used_by_default(self):
        config = self.config_class()
        assert config.SQLALCHEMY_DATABASE_URI == 'sqlite:///:memory:'

    def test_exception_is_raised_when_database_does_not_exist(self, tmpdir):
        db_path = tmpdir.join('test.db')

        with pytest.raises(FileNotFoundError):
            self.config_class(DATABASE_PATH=db_path)


class TestTestingConfig(BaseTestConfig):
    config_class = config.TestingConfig

import flask
import jinja2
import pytest

import website
# Rename TestingConfig to avoid Pytest to collect it.
from website.config import TestingConfig as _TestingConfig


class TestApplicationFactory:
    def test_all_blueprints_are_registered(self):
        app = website.create_app(_TestingConfig)
        assert 'blog' in app.blueprints

    def test_extensions_are_initialized(self):
        app = website.create_app(_TestingConfig)
        assert 'sqlalchemy' in app.extensions

    def test_jinja2_does_not_silently_pass_undefined_variables(self):
        app = website.create_app(_TestingConfig)

        with pytest.raises(jinja2.exceptions.UndefinedError):
            with app.test_request_context():
                flask.render_template_string('{{ undefined_variable }}')

    def test_set_config(self):
        class TestConfig(_TestingConfig):
            CLASS_CONFIG_KEY = 'class'

            def __init__(self):
                super().__init__()
                self.INSTANCE_CONFIG_KEY = 'instance'

        # A config class should be instantiated.
        app = website.create_app(TestConfig)
        assert app.config['CLASS_CONFIG_KEY'] == 'class'
        assert app.config['INSTANCE_CONFIG_KEY'] == 'instance'

        # And a config instance used as is.
        app = website.create_app(TestConfig())
        assert app.config['CLASS_CONFIG_KEY'] == 'class'
        assert app.config['INSTANCE_CONFIG_KEY'] == 'instance'

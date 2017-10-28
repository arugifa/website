import flask
import jinja2
import pytest

from website import helpers
# Rename TestingConfig to avoid Pytest to collect it.
from website.config import TestingConfig as _TestingConfig


class TestApplicationFactory:
    def test_all_blueprints_are_registered(self):
        app = helpers.create_app(_TestingConfig)
        assert 'website' in app.blueprints

    def test_extensions_are_initialized(self):
        app = helpers.create_app(_TestingConfig)
        assert 'sqlalchemy' in app.extensions

    def test_jinja2_does_not_silently_pass_undefined_variables(self):
        app = helpers.create_app(_TestingConfig)

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
        app = helpers.create_app(TestConfig)
        assert app.config['CLASS_CONFIG_KEY'] == 'class'
        assert app.config['INSTANCE_CONFIG_KEY'] == 'instance'

        # And a config instance used as is.
        app = helpers.create_app(TestConfig())
        assert app.config['CLASS_CONFIG_KEY'] == 'class'
        assert app.config['INSTANCE_CONFIG_KEY'] == 'instance'


def test_create_articles(db):
    articles = helpers.create_articles(3)

    assert len(articles) == 3

    # As in real life, recently written articles should have
    # a publication date/primary key more recent/higher
    # than older ones.

    assert articles[0].publication < \
           articles[1].publication < \
           articles[2].publication

    assert articles[0].id < articles[1].id < articles[2].id

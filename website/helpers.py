from datetime import date, timedelta
import inspect

from flask import Flask
import jinja2
from werkzeug.datastructures import ImmutableDict

from .factories import ArticleFactory
from .models import db
from .views import website


def create_app(config):
    app = Flask(__name__)

    if inspect.isclass(config):
        config = config()

    app.config.from_object(config)

    # In order to not partially render content of web pages,
    # the template engine must raise an exception for undefined variables.
    app.jinja_options = ImmutableDict(
        undefined=jinja2.StrictUndefined, **app.jinja_options)

    # Initialize application.
    db.init_app(app)
    app.register_blueprint(website)

    return app


def create_articles(count):
    """Create blog articles, with different publication dates.

    Articles are sorted by publication date, in ascending order.

    :param int count: number of articles to create.
    """
    today = date.today()
    return [
        ArticleFactory(publication=today - timedelta(days=days))
        for days in range(count, 0, -1)]

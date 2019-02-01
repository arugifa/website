import inspect

import jinja2
from flask import Blueprint, Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.datastructures import ImmutableDict

from .config import IN_MEMORY_DATABASE

# Disable autoflush to have more control over objects creation.
# Otherwise, when querying the database, SQLAlchemy can tries at the same time
# to flush uncompleted objects, which can then raises integrity errors.
db = SQLAlchemy(session_options={"autoflush": False})
website = Blueprint('website', __name__)


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

    if app.config['SQLALCHEMY_DATABASE_URI'] == IN_MEMORY_DATABASE:
        with app.app_context():
            db.create_all()

    from .blog import blog
    app.register_blueprint(blog)

    # from .notes import notes
    # app.register_blueprint(notes, url_prefix='/notes')

    # from .recommended import recommended
    # app.register_blueprint(recommended, url_prefix='/recommended')

    return app


from . import views  # noqa: E402, F401

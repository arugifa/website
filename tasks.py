"""Command-line utilities to manage my website updates and deployment."""

import logging
from pathlib import Path
from sys import exit

from flask_frozen import Freezer
from git.exc import GitError
from invoke import Task, task

from website import create_app, db as _db
from website.blog.handlers import ArticleFileHandler
from website.config import DevelopmentConfig
from website.demo import setup_demo
from website.handlers import CategoriesFileHandler, TagsFileHandler

here = Path(__file__).parent
logger = logging.getLogger(__name__)

SOURCE_CODE = here / 'website'
CSS_FILE = SOURCE_CODE / 'static/stylesheet.css'
FLASK_APP = here / 'manage.py'
FROZEN_WEBSITE = here / 'freezer'
SASS_FILE = here / 'stylesheets/main.scss'


class VerboseTask(Task):
    """Base class to provide a verbose mode to a specific task.

    Can be used as follows::

        @task(klass=VerboseTask)
        def my_task(ctx):
            ...
    """

    def __call__(self, *args, **kwargs):
        """Configure :mod:`logging` to display ``INFO`` logs when calling the task."""
        verbose = kwargs.pop('verbose')

        if verbose:
            logging.basicConfig(format='%(message)s', level=logging.INFO)

        return super().__call__(*args, **kwargs)

    def argspec(self, body):
        """Add a verbose flag to the task."""
        arg_names, spec_dict = super().argspec(body)

        arg_names.append('verbose')
        spec_dict['verbose'] = False

        return arg_names, spec_dict


# Development Server

@task
def run(ctx):
    """Run the website.

    The web server can be accessed on http://localhost:5000/

    Let Flask runs the server, otherwise automatic reloading does not work
    properly. See http://flask.pocoo.org/docs/latest/api/#flask.Flask.run
    for more info.
    """
    # Cannot type commands in the interpreter.
    # env = {'FLASK_APP': FLASK_APP, 'FLASK_DEBUG': '1'}
    # ctx.run('flask run', env=env)
    app = create_app(DevelopmentConfig)
    app.run(debug=True)


# Demo Server

@task
def demo(ctx):
    """Launch a demo server, with some data to play with.

    The server can be accessed on http://localhost:5000/
    """
    app = create_app(DevelopmentConfig)

    if not app.config['DATABASE_PATH']:
        # To not overwrite a database set via environment variables.
        setup_demo(app)

    app.run(debug=True, use_reloader=False)


# Utils

@task
def compile_css(ctx, css_file=CSS_FILE, style='compact'):
    """Compile SASS files to a CSS stylesheet."""
    # TODO: Add current date as suffix (03/2019)
    # In order to not have missing styles when updating static files online.
    ctx.run(f'sassc -t {style} {SASS_FILE} {css_file}')


@task
def create_db(ctx, path):
    """Create and initialize database."""
    path = Path(path)

    if path.exists():
        exit("💥 Database already exists!")

    path.touch()
    config = DevelopmentConfig(DATABASE_PATH=path)
    app = create_app(config)

    with app.app_context():
        _db.create_all()


@task(klass=VerboseTask)
def update(ctx, db, repository, commit='HEAD~1', force=False):
    """Update website's content from a content repository."""
    config = DevelopmentConfig(DATABASE_PATH=db)
    app = create_app(config)

    asciidoctor = AsciidoctorToHTMLConverter()
    handlers = {
        'categories.yml': CategoriesFileHandler,
        'tags.yml': TagsFileHandler,
        'blog/**/*.adoc': partial(ArticleFileHandler, reader=asciidoctor),
    }

    async def main(content):
        repository = Repository(repository)  # Can raise GitError
        content = ContentManager(repository, handlers)

        with content.load_changes(since=commit) as update:
            await update.plan(show_preview=true)  # Can raise ContentUpdatePlanFailure

            if not force:
                update.confirm()  # Can raise UpdateAborted

            await update.run(show_report=true)  # Can raise ContentUpdateResultFailure

    with app.app_context(), suppress(UpdateAborted):
        try:
            asyncio.run(main(content))
        except (GitError, ContentUpdatePlanFailure, ContentUpdateResultFailure) as exc:
            _db.session.rollback()
            sys.exit(exc)
        else:
            _db.session.commit()


# Deployment

@task
def freeze(ctx, dst=FROZEN_WEBSITE, preview=False):
    config = DevelopmentConfig(FREEZER_DESTINATION=dst)
    app = create_app(config)
    freezer = Freezer(app)

    if preview:
        freezer.run(debug=True)
    else:
        freezer.freeze()
        print(f"Website frozen in {freezer.root}")

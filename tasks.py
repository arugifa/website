"""Command-line utilities to manage my website updates and deployment."""

import logging
from functools import partial
from pathlib import Path
from sys import exit, stdout

from flask_frozen import Freezer
from invoke import task
from rackspace.connection import Connection as CloudConnection

from website import create_app, db as _db
from website.blog.content import ArticleHandler
from website.cloud import CloudManager
from website.config import DevelopmentConfig
from website.content import ContentManager
from website.exceptions import ContentUpdateException
from website.git import Repository
from website.helpers import setup_demo
from website.stubs import CloudConnectionStub
from website.utils.asciidoctor import AsciidoctorToHTMLConverter

here = Path(__file__).parent
logger = logging.getLogger(__name__)

SOURCE_CODE = here / 'website'
CSS_FILE = SOURCE_CODE / 'static/stylesheet.css'
FLASK_APP = here / 'manage.py'
FROZEN_WEBSITE = here / 'frozen'
SASS_FILE = SOURCE_CODE / 'stylesheets/main.scss'

PRODUCTION = {'cloud': CloudConnection}
TESTING = {'cloud': CloudConnectionStub}

logging.basicConfig(format='%(message)s', level=logging.INFO)


# Development Servers

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
    ctx.run(f'sassc -t {style} {SASS_FILE} {css_file}')


@task
def create_db(ctx, path):
    """Create and initialize database."""
    path = Path(path)

    if path.exists():
        exit("Database already exists!")

    path.touch()
    config = DevelopmentConfig(DATABASE_PATH=path)
    app = create_app(config)

    with app.app_context():
        _db.create_all()


@task
def update(ctx, db, repository, commit='HEAD~1', force=False):
    """Update website's content from a content repository."""
    config = DevelopmentConfig(DATABASE_PATH=db)
    app = create_app(config)

    # Get list of modified documents in the repository.
    repository = Repository(repository)
    invoke_shell = partial(ctx.run, hide='stdout')
    diff = repository.diff(commit, shell=invoke_shell, output=stdout)

    if not force:
        confirm()

    # Update documents in database.
    handlers = {'blog': ArticleHandler}
    reader = AsciidoctorToHTMLConverter(invoke_shell)
    content = ContentManager(handlers, reader)

    with app.app_context():
        try:
            content.update(repository.path, diff)
        except ContentUpdateException:
            _db.session.rollback()
            logger.error("No change has been made to the database")
        else:
            _db.session.commit()


# Deployment

@task
def freeze(ctx, dest=FROZEN_WEBSITE, preview=False):
    config = DevelopmentConfig(FREEZER_DESTINATION=dest)
    app = create_app(config)
    freezer = Freezer(app)

    if preview:
        freezer.run(debug=True)
    else:
        freezer.freeze()
        print(f"Website frozen in {freezer.root}")


@task
def deploy(ctx, user_name, api_key, region, container_name, noop=False):
    app = create_app(DevelopmentConfig)
    static_files = app.config['FREEZER_DESTINATION']

    cloud = TESTING['cloud'] if noop else PRODUCTION['cloud']

    try:
        website = CloudManager(user_name, api_key, region, cls=cloud)
        website.update(static_files)
    except CloudConnectionError as exc:
        exit("Seems like there are some perturbations in the Cloud today! :o")


# Helpers
# =======

def confirm():
    answer = input("Do you want to continue? [Y/n] ")
    if answer.lower() == 'n':
        exit()

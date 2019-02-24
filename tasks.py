"""Command-line utilities to manage my website updates and deployment."""

import logging
import sys
from functools import partial
from pathlib import Path
from sys import exit

import openstack
from flask_frozen import Freezer
from invoke import task

from website import create_app, db as _db, exceptions
from website.blog.content import ArticleHandler
from website.cloud import CloudManager
from website.config import DevelopmentConfig
from website.content import ContentManager
from website.helpers import setup_demo
from website.stubs import cloud_stub_factory
from website.utils.asciidoctor import AsciidoctorToHTMLConverter
from website.utils.git import Repository

here = Path(__file__).parent
logger = logging.getLogger(__name__)

SOURCE_CODE = here / 'website'
CSS_FILE = SOURCE_CODE / 'static/stylesheet.css'
FLASK_APP = here / 'manage.py'
FROZEN_WEBSITE = here / 'frozen'
SASS_FILE = SOURCE_CODE / 'stylesheets/main.scss'

PRODUCTION = {'cloud': openstack.connect}
TESTING = {'cloud': cloud_stub_factory}

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
    invoke_shell = partial(ctx.run, hide='stdout')
    repository = Repository(repository, shell=invoke_shell)
    diff = repository.diff(commit, quiet=False)

    if not force:
        confirm()

    # Update documents in database.
    handlers = {'blog': ArticleHandler}
    reader = AsciidoctorToHTMLConverter(invoke_shell)
    content = ContentManager(repository.path, handlers, reader)

    with app.app_context():
        try:
            content.update(diff)
        except ContentUpdateException:
            _db.session.rollback()
            print("No change has been made to the database")
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


@task
def deploy(ctx, website=FROZEN_WEBSITE, container='website', noop=False):
    environment = TESTING['cloud'] if noop else PRODUCTION['cloud']

    try:
        cloud = CloudManager(website, container, environment)
    except exceptions.CloudConnectionFailure as exc:
        sys.exit(f"Cannot connect to the Cloud: {exc}")

    try:
        cloud.update()
    except CloudConnectionError as exc:
        exit("Seems like there are some perturbations in the Cloud today! :o")


# Helpers
# =======

def confirm():
    answer = input("Do you want to continue? [Y/n] ")
    if answer.lower() == 'n':
        exit()

"""Command-line utilities to manage my website updates and deployment."""

import asyncio
import logging
import sys
from contextlib import suppress
from functools import partial
from pathlib import Path
from sys import exit

import openstack
from flask_frozen import Freezer
from invoke import task

from website import create_app, db as _db
from website.blog.content import ArticleHandler
from website.cloud import CloudUpdateManager
from website.config import DevelopmentConfig
from website.content import ContentUpdateManager
from website.exceptions import (
    CloudConnectionFailure, CloudContainerNotFound, ContentUpdateException,
    NoUpdate, UpdateAborted)
from website.helpers import setup_demo
from website.stubs import CloudStubConnectionFactory
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
TESTING = {'cloud': CloudStubConnectionFactory}


class VerboseTask(Task):
    def __call__(self, *args, **kwargs):
        verbose = kwargs.pop('verbose')

        if verbose:
            logging.basicConfig(format='%(message)s', level=logging.INFO)

        return super().__call__(*args, **kwargs)

    def argspec(self, body):
        arg_names, spec_dict = super().argspec(body)

        arg_names.append('verbose')
        spec_dict['verbose'] = False

        return arg_names, spec_dict


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
    # TODO: Add current date as a suffix (03/2019)
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

    repository = Repository(repository)
    handlers = {'blog': ArticleHandler}
    asciidoctor = AsciidoctorToHTMLConverter()
    content = ContentUpdateManager(repository, handlers, reader=asciidoctor)

    async def main(content):
        # In tests: content.update(repository).run()
        async with content.update(commit) as update:
            update.confirm()
            await update.proceed()

    with app.app_context(), suppress(UpdateAborted):
        try:
            asyncio.run(main(content))

        except ContentUpdateException as error:
            _db.session.rollback()

            print(f"💣 {error}")
            print("No change has been made to the database")

        except NoUpdate:
            print("Nothing to update 💤")

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


@task(klass=VerboseTask)
def deploy(ctx, website=FROZEN_WEBSITE, container='website', noop=False):

    def main(cloud):
        async with cloud.update(website) as update:
            update.confirm()
            await update.proceed()

    try:
        connection = TESTING['cloud']() if noop else PRODUCTION['cloud']()
        cloud = CloudUpdateManager(connection, container)

        with suppress(UpdateAborted):
            asyncio.run(main(cloud))

    except CloudConnectionFailure as exc:
        sys.exit(f"⛈ Cannot connect to the Cloud: {exc}")

    except CloudContainerNotFound:
        sys.exit(
            f'⛔ You must manually create and configure '
            f'the "{container}" container before deploying the website')

    except NoUpdate:
        print("Nothing to update 💤")

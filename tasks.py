"""Command-line utilities to manage my website updates and deployment."""

import logging
import sys
from functools import partial
from pathlib import Path
from sys import exit

from flask_frozen import Freezer
from invoke import task
from openstack.exceptions import SDKException
from rackspace.connection import Connection

from website import create_app, db as _db
from website.cloud.stubs import ConnectionStub
from website.cloud.utils import (
    connect_to_the_cloud, delete_outdated_files, retrieve_container,
    retrieve_objects, upload_existing_files, upload_new_files)
from website.config import DevelopmentConfig
from website.content import ContentManager
from website.utils import git
from website.utils.asciidoctor import AsciidoctorToHTMLConverter
from website.utils.demo import setup_demo

here = Path(__file__).parent

SOURCE_CODE = here / 'website'
CSS_FILE = SOURCE_CODE / 'static/stylesheet.css'
FLASK_APP = here / 'manage.py'
FROZEN_WEBSITE = here / 'frozen'
SASS_FILE = SOURCE_CODE / 'stylesheets/main.scss'

logging.basicConfig(format='%(message)s', level=logging.INFO)


# Helper Functions

def confirm():
    answer = input("Do you want to continue? [Y/n] ")
    if answer.lower() == 'n':
        exit()


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

    repository = Path(repository).resolve()
    invoke_shell = partial(ctx.run, hide='stdout')

    # Get list of modified documents in the repository.
    with ctx.cd(repository):
        diff = git.diff(commit, shell=invoke_shell)

    if not force:
        confirm()

    # Update documents in database.
    content_reader = AsciidoctorToHTMLConverter(invoke_shell)
    content = ContentManager(repository, content_reader)

    with app.app_context():
        try:
            content.add(diff['added'])
            content.update(diff['modified'])
            content.rename(diff['renamed'])
            content.delete(diff['deleted'])

            _db.session.commit()

        except Exception:
            _db.session.rollback()
            exit("No change has been made to the database")


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
        print(f"Site frozen in {freezer.root}")


@task
def deploy(ctx, user_name, api_key, region, container_name, noop=False):
    connection_class = ConnectionStub if noop else Connection

    # Retrieve list of remote files.
    try:
        connection = connect_to_the_cloud(
            user_name, api_key, region, connection_class)
        cloud = connection.object_store
        container = retrieve_container(cloud, container_name)

        if container is None:
            exit(f'Container "{container_name}" not found!')

        objects = retrieve_objects(cloud, container)
    except SDKException as exc:
        exit("Seems like there are some perturbations in the Cloud today! :o")

    remote_files = set(objects)

    # Retrieve list of local files.
    app = create_app(DevelopmentConfig)

    frozen_path = app.config['FREEZER_DESTINATION']
    frozen_files = {
        str(f.relative_to(frozen_path)): f
        for f in frozen_path.rglob('*') if f.is_file()}

    local_files = set(frozen_files)

    # Update remote files.
    to_delete = remote_files - local_files
    to_add = {
        f: frozen_files[f] for f in local_files - remote_files}
    to_update = {
        f: frozen_files[f] for f in local_files - set(to_add)}

    upload_new_files(cloud, container, to_add)
    upload_existing_files(cloud, container, to_update)
    delete_outdated_files(cloud, container, to_delete)

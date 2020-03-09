import os
import signal
import time
from subprocess import CalledProcessError

import pytest
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError

from arugifa.website import create_app, db as _db
from arugifa.website.config import DevelopmentConfig

WEB_SERVER_URL = 'http://localhost:5000'


# Tests

def test_compile_css(invoke, sass, tmpdir):
    css = tmpdir.join('stylesheet.css')
    invoke.run(f'compile-css --css-file {css}')
    assert css.size() > 0


class TestCreateDB:
    def test_create_new_db(self, invoke, tmpdir):
        db = tmpdir.join('test.db')
        invoke.run(f'create-db {db}')
        assert db.size() > 0

    def test_cannot_overwrite_existing_db(self, invoke, tmpdir):
        db = tmpdir.join('test.db')
        db.ensure()

        with pytest.raises(CalledProcessError):
            invoke.run(f'create-db {db}', check=True)


class TestFreeze:
    def test_freeze(self, invoke, tmpdir):
        frozen = tmpdir.join('frozen')
        invoke.run(f'freeze --dst {frozen}')

        assert frozen.check() is True
        assert len(frozen.listdir()) > 0

    def test_preview(self, invoke):
        check_server_is_running(invoke, 'freeze --preview')


class TestDemo:
    def test_in_memory_database_is_populated(self, invoke):
        response = check_server_is_running(invoke, 'demo')
        assert len(response.select('.article-list__item')) > 0

    def test_on_disk_database_is_not_overwritten(self, invoke, monkeypatch, tmpdir):
        db = tmpdir.ensure('test.db')
        config = DevelopmentConfig(DATABASE_PATH=db)
        app = create_app(config)

        with app.app_context():
            _db.create_all()
        last_update = db.mtime()

        monkeypatch.setenv(DevelopmentConfig.ENV_DATABASE_PATH, str(db))
        check_server_is_running(invoke, 'demo')

        assert db.mtime() == last_update


def test_run(invoke):
    check_server_is_running(invoke, 'run')


# Helpers

def check_server_is_running(invoke, task):
    # Thanks to https://pymotw.com/2/subprocess/#process-groups-sessions
    server = invoke.run_with_popen(
        task,
        preexec_fn=os.setsid)  # To kill web server launched as a child process

    try:
        for retry in range(19, -1, -1):
            # We have to wait for the web server to be fully launched.
            # Waiting for 2 seconds maximum is a completely arbitrary choice.
            try:
                # Should not raise.
                response = requests.get(WEB_SERVER_URL)
                response.raise_for_status()
            except ConnectionError as exc:
                if not retry:
                    raise exc
                time.sleep(0.1)
            else:
                return BeautifulSoup(response.text, 'html.parser')
    finally:
        os.killpg(server.pid, signal.SIGTERM)

import os
from pathlib import PurePath
import signal
from subprocess import CalledProcessError, Popen
import time

import pytest
import requests
from requests.exceptions import ConnectionError

from website.config import DevelopmentConfig


# Tests

def test_compile_css(invoke, tmpdir):
    css = tmpdir.join('stylesheet.css')
    invoke.run(f'compile-css --css-file {css}')
    assert css.size() > 0


class TestCreateDB:
    def test_create_new_db(self, invoke, tmpdir):
        db = tmpdir.join('test.db')
        invoke.run(f'create-db {db}')
        assert db.size() > 0

    def test_overwrite_db(self, invoke, tmpdir):
        db = tmpdir.join('test.db')
        db.ensure()

        with pytest.raises(CalledProcessError):
            invoke.run(f'create-db {db}', check=True)


class TestFreeze:
    def test_freeze(self, invoke, tmpdir):
        frozen = tmpdir.join('frozen')
        invoke.run(f'freeze --dest {frozen}')

        assert frozen.check() > 0
        assert len(frozen.listdir()) > 0

    def test_preview(self, invoke, monkeypatch):
        check_server('freeze --preview', monkeypatch)


def test_demo(invoke, monkeypatch):
    check_server('demo', monkeypatch)


def test_run(invoke, monkeypatch):
    check_server('run', monkeypatch)


# Helpers

def check_server(cmdline, monkeypatch):
    # Ensure WEBSITE_DB is not set before launching the demo server.
    # Otherwise, a prompt would be displayed to confirm overwriting
    # the database if exists.
    monkeypatch.delenv(
        DevelopmentConfig.DATABASE_USER_PATH_ENV, raising=False)

    cmdline = cmdline.split()
    cmdline.insert(0, 'invoke')

    # Thanks to https://pymotw.com/2/subprocess/#process-groups-sessions
    server = Popen(
        cmdline,
        preexec_fn=os.setsid)  # To kill child processes

    try:
        for retry in range(19, -1, -1):
            # We have to wait for the web server to be fully launched.
            # Waiting for 2 seconds maximum is a completely arbitrary choice.
            try:
                # Should not raise.
                requests.get('http://localhost:5000').raise_for_status()
            except ConnectionError as exc:
                if not retry:
                    raise exc
                time.sleep(0.1)
            else:
                break
    finally:
        os.killpg(server.pid, signal.SIGTERM)

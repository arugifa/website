My Website
==========

Requirements:

- `Asciidoctor <http://asciidoctor.org/>`_
- `Bower <https://bower.io/>`_
- `Geckodriver <https://github.com/mozilla/geckodriver>`_
- `Tox <https://tox.readthedocs.io/>`_

To launch the tests::

    $ tox

To play with the web application::

    $ tox -e dev
    $ source venv/bin/activate

    $ pytest  # To launch the tests manually

    $ export FLASK_APP=manage.py
    $ flask demo   # To launch the demo server
    $ flask shell  # To interact with the application

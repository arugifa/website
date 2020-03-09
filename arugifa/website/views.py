"""Global web pages of my website."""

from flask import render_template

from arugifa.website import website


@website.route('/404error.html')
def page_not_found_on_the_cloud():  # noqa: D401
    """Generic HTTP 404 Not Found error page.

    We define a specific view instead of using :meth:`website.app_errorhandler` to
    handle 404 errors. The reason is simple: when uploading the website to the Cloud
    (as a set of static files), OpenStack Swift expects a file named ``404error.html``
    to exist.
    """
    return render_template('404.html'), 404

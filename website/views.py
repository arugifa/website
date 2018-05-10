from flask import render_template

from . import website


@website.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@website.route('/404error.html')
def page_not_found_on_rackspace():
    """404 page needed to host a static website on RackSpace."""
    return render_template('404.html'), 404

from flask import Blueprint, abort, render_template

from .models import Article

# Even if the website doesn't need to be modular,
# we create a blueprint here as we cannot access to
# the Flask application directly. Indeed, this latter
# is created with a factory, in order to modify settings
# during tests execution.
website = Blueprint('website', __name__)


@website.route('/')
def home():
    articles = Article.latest()
    return render_template('home.html', articles=articles)


@website.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@website.route('/404error.html')
def page_not_found_on_rackspace():
    """404 page needed to host a static website on RackSpace."""
    return render_template('404.html'), 404


@website.route('/articles/<uri>.html')
def article(uri):
    article = Article.find(uri=uri)

    if article is None:
        abort(404)

    return render_template('article.html', article=article)


"""
@website.route('/recommended')
def recommended():
    raise NotImplementedError


@website.route('/life_notes')
def life_notes():
    raise NotImplementedError
"""

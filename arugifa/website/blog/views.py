"""Blog's web pages."""

from flask import abort, render_template

from arugifa.website.blog import blog
from arugifa.website.blog.models import Article
from arugifa.website.exceptions import ItemNotFound


@blog.route('/')
def home():
    """Blog home page."""
    articles = Article.latest_ones()
    return render_template('blog.html', articles=articles)


@blog.route('/articles/<uri>.html')
def article(uri):
    """Blog article page."""
    try:
        article = Article.find(uri=uri)
    except ItemNotFound:
        abort(404)

    return render_template('article.html', article=article)

from flask import abort, render_template

from website.blog import blog
from website.blog.models import Article


@blog.route('/')
def home():
    """Blog home page."""
    articles = Article.latest_ones()
    return render_template('blog.html', articles=articles)


@blog.route('/articles/<uri>.html')
def article(uri):
    """Blog article page."""
    article = Article.find(uri=uri)

    if article is None:
        abort(404)

    return render_template('article.html', article=article)

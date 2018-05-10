from flask import abort, render_template

from . import blog
from .models import Article


@blog.route('/')
def home():
    articles = Article.latest()
    return render_template('blog.html', articles=articles)


@blog.route('/articles/<uri>.html')
def article(uri):
    article = Article.find(uri=uri)

    if article is None:
        abort(404)

    return render_template('article.html', article=article)

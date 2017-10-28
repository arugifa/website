from datetime import date
from pathlib import PurePath
from textwrap import dedent

from bs4 import BeautifulSoup

from website.utils import blog as utils


def test_add_article():
    path = PurePath('blog/2018/04-08.article.adoc')
    content = dedent("""\
        <h1>Article Title</h1>
        <div id="preamble">
        <div class="sectionbody">
        <div class="paragraph">
        <p>This is the article teaser.</p>
        </div>
        </div>
        </div>
        <div class="sect1">
        <h2 id="_section">Section</h2>
        <div class="sectionbody">
        <div class="paragraph">
        <p>This is the main part.</p>
        </div>
        </div>
        </div>
         """)

    article = utils.add_article(path, content)

    assert article.title == "Article Title"
    assert article.teaser == "This is the article teaser."
    assert article.content == content
    assert article.publication == date(2018, 4, 8)


def test_retrieve_article_title():
    content = '<h1>Article Title</h1>'
    soup = BeautifulSoup(content, 'html.parser')
    title = utils.retrieve_article_title(soup)
    assert title == 'Article Title'


def test_retrieve_article_teaser():
    content = '<div id="preamble">This is the article teaser.</div>'
    soup = BeautifulSoup(content, 'html.parser')
    teaser = utils.retrieve_article_teaser(soup)
    assert teaser == 'This is the article teaser.'

from datetime import date

from bs4 import BeautifulSoup

from website.blog.models import Article

from .documents import retrieve_document_date, retrieve_document_uri


# XXX: If it is necessary to ask for tags to the user later on,
# just provide an ask parameter, which can be easily replaced
# during tests with a stub :ok_hand:
#
# def add_article(path, content, ask=input):
#     tags = ask("Article's tags (separated by a comma): ")
#     article.tags = tags.split(',')


def add_article(path, content):
    content = BeautifulSoup(content, 'html.parser')

    uri = retrieve_document_uri(path)
    title = retrieve_article_title(content)
    teaser = retrieve_article_teaser(content)
    date = retrieve_document_date(path)

    return Article(
        content=str(content), publication=date,
        teaser=teaser, title=title, uri=uri)


def update_article(article, path, content):
    content = BeautifulSoup(content, 'html.parser')

    article.uri = retrieve_document_uri(path)
    article.title = retrieve_article_title(content)
    article.teaser = retrieve_article_teaser(content)
    article.content = str(content)
    article.last_update = date.today()


def retrieve_article_title(content):
    return content.select_one('h1').text


def retrieve_article_teaser(content):
    return content.select_one('#preamble').text.strip()

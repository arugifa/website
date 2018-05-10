from datetime import date

from bs4 import BeautifulSoup

from website import db
from website.models import Tag
from website.utils.asciidoctor import (
    look_for_category, look_for_content,
    look_for_introduction, look_for_tags, look_for_title)

from .documents import retrieve_document_date, retrieve_document_uri
from .models import Article, Category


def add_article(path, src, prompt=input):
    uri = retrieve_document_uri(path)
    date = retrieve_document_date(path)

    html = BeautifulSoup(src, 'html.parser')
    title = look_for_title(html)
    introduction = look_for_introduction(html)
    content = look_for_content(html)

    category_uri = look_for_category(html)
    category = insert_category(category_uri, prompt)

    tag_uris = look_for_tags(html)
    tags = insert_tags(tag_uris, prompt)

    return Article(
        title=title, uri=uri,
        category=category, tags=tags,
        introduction=introduction, content=content,
        publication_date=date)


def update_article(path, src, prompt=input):
    uri = retrieve_document_uri(path)
    article = Article.find(uri=uri)

    html = BeautifulSoup(src, 'html.parser')
    article.title = look_for_title(html)
    article.introduction = look_for_introduction(html)
    article.content = look_for_content(html)

    category_uri = look_for_category(html)
    article.category = insert_category(category_uri, prompt)

    tag_uris = look_for_tags(html)
    article.tags = insert_tags(tag_uris, prompt)

    article.last_update = date.today()

    return article


def rename_article(previous_path, new_path, src, prompt=input):
    # Can set an HTTP redirection.
    previous_uri = retrieve_document_uri(previous_path)
    article = Article.find(uri=previous_uri)

    new_uri = retrieve_document_uri(new_path)
    article.uri = new_uri

    update_article(new_path, src, prompt)


def delete_article(path):
    # Can clean orphan tags.
    uri = retrieve_document_uri(path)
    article = Article.find(uri=uri)
    db.session.delete(article)


def insert_category(uri, ask=input):
    category = Category.find(uri=uri)

    if not category:
        name = ask('Please enter a name for the new "{tag}" category: ')
        category = Category(name=name, uri=uri)
        category.save()

    return category


def insert_tags(uris, ask=input):
    tags = Tag.filter(uri=uris).all()

    existing = set([tag.uri for tag in tags])
    new = set(uris) - existing

    for uri in new:
        name = ask('Please enter a name for the new "{tag}" tag: ')
        tag = Tag(name=name, uri=uri)
        tag.save()
        tags.append(tag)

    return tags

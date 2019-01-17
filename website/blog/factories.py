"""Factories to create blog articles during testing."""

from datetime import date

from factory import LazyFunction, List, Sequence, SubFactory

from website.blog import models
from website.factories import BaseDatabaseFactory


class ArticleFactory(BaseDatabaseFactory):
    class Meta:
        model = models.Article

    uri = Sequence(lambda n: f'article_{n}')

    title = Sequence(lambda n: f"Article {n}")
    introduction = "This is the article's introduction."
    content = "<p>This is the article's content.</p>"

    publication_date = LazyFunction(date.today)
    last_update = None

    category = SubFactory('website.blog.factories.CategoryFactory')
    tags = List([
        SubFactory('website.blog.factories.TagFactory') for _ in range(2)])


class CategoryFactory(BaseDatabaseFactory):
    class Meta:
        model = models.Category

    uri = Sequence(lambda n: f'category_{n}')
    name = Sequence(lambda n: f"Category {n}")


class TagFactory(BaseDatabaseFactory):
    class Meta:
        model = models.Tag

    uri = Sequence(lambda n: f'tag_{n}')
    name = Sequence(lambda n: f"Tag {n}")

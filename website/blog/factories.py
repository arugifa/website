"""Blog's factories to create dynamic fixtures during testing."""

from datetime import date

from factory import LazyFunction, List, Sequence, SubFactory

from website.blog import models
from website.factories import BaseDatabaseFactory


class ArticleFactory(BaseDatabaseFactory):
    class Meta:
        model = models.Article

    uri = Sequence(lambda n: f'article_{n+1}')  # Don't start from 0 during demo

    title = Sequence(lambda n: f"Article {n+1}")
    lead = "Grab reader's attention."
    body = "<p>This is the article's content.</p>"

    publication_date = LazyFunction(date.today)
    last_update = None

    category = SubFactory('website.blog.factories.CategoryFactory')
    tags = List([SubFactory('website.blog.factories.TagFactory') for _ in range(2)])


class CategoryFactory(BaseDatabaseFactory):
    class Meta:
        model = models.Category

    uri = Sequence(lambda n: f'category_{n+1}')  # Don't start from 0 during demo
    name = Sequence(lambda n: f"Category {n+1}")


class TagFactory(BaseDatabaseFactory):
    class Meta:
        model = models.Tag

    uri = Sequence(lambda n: f'tag_{n+1}')  # Don't start from 0 during demo
    name = Sequence(lambda n: f"Tag {n+1}")

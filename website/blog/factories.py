"""Blog's factories to create dynamic fixtures during testing."""

from datetime import date

from factory import LazyFunction, Sequence

from website.base.factories import BaseDocumentFactory
from website.blog.models import Article


class ArticleFactory(BaseDocumentFactory):
    class Meta:
        model = Article

    uri = Sequence(lambda n: f'article_{n+1}')  # Don't start from 0 during demo

    title = Sequence(lambda n: f"Article {n+1}")
    lead = "Grab reader's attention."
    body = "<p>This is the article's content.</p>"

    publication_date = LazyFunction(date.today)
    last_update = None

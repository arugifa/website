from factory import List, Sequence, SubFactory

from website.models import blog as models

from .base import BaseSQLAlchemyFactory
from .documents import DocumentFactory, TagFactory


class CategoryFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.Category

    name = Sequence(lambda n: f"Category {n}")
    uri = Sequence(lambda n: f'category_{n}')


class ArticleFactory(DocumentFactory):
    class Meta:
        model = models.Article

    title = Sequence(lambda n: f"Article {n}")
    introduction = "This is the article's introduction."
    content = "<p>This is the article's content.</p>"
    category = SubFactory(CategoryFactory)
    tags = List([SubFactory(TagFactory) for _ in range(2)])
    uri = Sequence(lambda n: f'article_{n}')

from factory import Sequence

from arugifa.website.base.factories import BaseDatabaseFactory
from arugifa.website.models import Category, Tag


class CategoryFactory(BaseDatabaseFactory):
    class Meta:
        model = Category

    uri = Sequence(lambda n: f'category_{n+1}')  # Don't start from 0 during demo
    name = Sequence(lambda n: f"Category {n+1}")


class TagFactory(BaseDatabaseFactory):
    class Meta:
        model = Tag

    uri = Sequence(lambda n: f'tag_{n+1}')  # Don't start from 0 during demo
    name = Sequence(lambda n: f"Tag {n+1}")

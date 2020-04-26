from factory import Sequence

from website import models
from website.base.factories import BaseMetadataFactory


class CategoryFactory(BaseMetadataFactory):
    class Meta:
        model = models.Category

    uri = Sequence(lambda n: f'category_{n+1}')  # Don't start from 0 during demo
    name = Sequence(lambda n: f"Category {n+1}")


class TagFactory(BaseMetadataFactory):
    class Meta:
        model = models.Tag

    uri = Sequence(lambda n: f'tag_{n+1}')  # Don't start from 0 during demo
    name = Sequence(lambda n: f"Tag {n+1}")

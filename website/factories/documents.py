from datetime import date

from factory import LazyFunction, Sequence

from website.models import documents as models

from .base import BaseSQLAlchemyFactory


class DocumentFactory(BaseSQLAlchemyFactory):
    class Meta:
        abstract = True

    publication_date = LazyFunction(date.today)
    last_update = None


class TagFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.Tag

    name = Sequence(lambda n: f"Tag {n}")
    uri = Sequence(lambda n: f'tag_{n}')

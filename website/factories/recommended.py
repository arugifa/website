from factory import Sequence

from website.models import recommended as models

from .base import BaseSQLAlchemyFactory


class RecommendedArticleFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.RecommendedArticle

    title = Sequence(lambda n: f"Recommended Article {n}")
    summary = "This is a recommended article."
    url = Sequence(lambda n: f'http://www.medium.com/{n}')


class RecommendedBookFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.RecommendedBook

    title = Sequence(lambda n: f"Recommended Book {n}")
    summary = "This is a recommended video."
    url = Sequence(lambda n: f'http://www.oreilly.com/{n}')


class RecommendedVideoFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.RecommendedVideo

    title = Sequence(lambda n: f"Recommended Video {n}")
    summary = "This is a recommended video."
    url = Sequence(lambda n: f'http://www.youtube.com/{n}')

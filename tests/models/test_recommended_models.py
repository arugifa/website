from website.factories import recommended as factories
from website.models import recommended as models
from website.test.models import BaseTestRecommendedModel


class TestRecommendedArticleModel(BaseTestRecommendedModel):
    factory = factories.RecommendedArticleFactory
    model = models.RecommendedArticle


class TestRecommendedBookModel(BaseTestRecommendedModel):
    factory = factories.RecommendedBookFactory
    model = models.RecommendedBook


class TestRecommendedVideoModel(BaseTestRecommendedModel):
    factory = factories.RecommendedVideoFactory
    model = models.RecommendedVideo

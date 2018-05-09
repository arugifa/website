from datetime import date, timedelta

from website.factories import blog as factories
from website.models import blog as models
from website.test.models import BaseTestDocumentModel, BaseTestModel


class TestArticleModel(BaseTestDocumentModel):
    factory = factories.ArticleFactory
    model = models.Article

    def test_retrieve_latest_articles(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        articles = [
            self.factory(publication_date=yesterday),
            self.factory(publication_date=today),
            self.factory(publication_date=today)]

        # Latest articles are sorted by publication date
        # and ID in descending order.
        expected = articles[::-1]
        actual = list(self.model.latest())
        assert actual == expected


class TestCategoryModel(BaseTestModel):
    factory = factories.CategoryFactory
    model = models.Category
    filterable_column = 'name'

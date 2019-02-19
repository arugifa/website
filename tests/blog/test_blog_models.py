from datetime import date, timedelta

from website.blog import factories, models

from tests._test_models import BaseTestDocumentModel, BaseTestModel  # noqa: E501, I100


class TestArticleModel(BaseTestDocumentModel):
    factory = factories.ArticleFactory
    model = models.Article
    optional_fields = ['last_update', 'publication_date']
    filterable_column = 'title'

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
        actual = list(self.model.latest_ones())
        assert actual == expected


class TestCategoryModel(BaseTestModel):
    factory = factories.CategoryFactory
    model = models.Category
    filterable_column = 'name'


class TestTagModel(BaseTestModel):
    factory = factories.TagFactory
    model = models.Tag
    filterable_column = 'name'

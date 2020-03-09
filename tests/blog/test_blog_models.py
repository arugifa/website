from datetime import date, timedelta

from arugifa.website.blog import factories, models
from arugifa.website.testing.models import BaseDocumentModelTest


class TestArticleModel(BaseDocumentModelTest):
    factory = factories.ArticleFactory
    model = models.Article
    doc_type = 'article'
    table = 'articles'

    def test_retrieve_latest_articles(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        articles = [
            self.factory(publication_date=yesterday),
            self.factory(publication_date=today),
            self.factory(publication_date=today)]

        # Latest articles are sorted by publication date and ID in descending order.
        expected = articles[::-1]
        actual = list(self.model.latest_ones())
        assert actual == expected

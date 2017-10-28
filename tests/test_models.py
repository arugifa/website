from datetime import date, timedelta
import re

import pytest

from website import factories
from website import models

pytestmark = pytest.mark.usefixtures('db')


class BaseTestModel:
    factory = None
    model = None
    optional_fields = None

    def test_optional_fields_do_not_have_to_bet_set(self):
        if self.optional_fields is None:
            pytest.skip("This model doesn't have optional fields")

        optional = {f: None for f in self.optional_fields}
        self.factory(**optional)  # Should not raise

    def test_table_name_is_model_name_in_plural(self):
        model_name = self.model.__name__
        model_name_plural = model_name + 's'
        table_name = self.model.__tablename__

        expected = re.sub('(?!^)([A-Z]+)', r'_\1', model_name_plural).lower()
        assert table_name == expected

    def test_retrieve_all_items(self):
        items = self.factory.create_batch(2)
        assert self.model.all() == items


# Documents

class BaseTestDocument(BaseTestModel):
    optional_fields = ['last_update', 'publication']

    def test_default_publication_date(self):
        document = self.factory(publication=None)
        assert document.publicatoin == date.today()


class TestArticle(BaseTestModel):
    factory = factories.ArticleFactory
    model = models.Article

    def test_retrieve_latest_articles(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        articles = [
            self.factory(publication=yesterday),
            self.factory(publication=today),
            self.factory(publication=today)]

        # Latest articles are sorted by publication date
        # and ID in descending order.
        expected = articles[::-1]
        actual = list(self.model.latest())
        assert actual == expected

    def test_find_article(self):
        expected = self.factory()
        actual = self.model.find(title=expected.title, uri=expected.uri)
        assert actual == expected

    def test_find_not_existing_article(self):
        assert self.model.find(title="I don't exist") is None

    def test_cannot_find_similar_articles(self):
        self.factory.create_batch(2, title='Blue Monday')
        with pytest.raises(models.MultipleResultsFound):
            self.model.find(title='Blue Monday')


class TestLifeNote(BaseTestModel):
    factory = factories.LifeNoteFactory
    model = models.LifeNote


# Recommended Material

class TestRecommendedArticle(BaseTestModel):
    factory = factories.RecommendedArticleFactory
    model = models.RecommendedArticle


class TestRecommendedBook(BaseTestModel):
    factory = factories.RecommendedBookFactory
    model = models.RecommendedBook


class TestRecommendedVideo(BaseTestModel):
    factory = factories.RecommendedVideoFactory
    model = models.RecommendedVideo

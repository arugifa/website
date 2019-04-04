from datetime import date, timedelta

from website.blog import factories, models

from tests._test_models import BaseTestDocumentModel, BaseTestModel  # noqa: E501, I100


class TestArticleModel(BaseTestDocumentModel):
    factory = factories.ArticleFactory
    model = models.Article
    doc_type = 'article'
    table = 'articles'

    def test_tag_list_is_always_sorted(self):
        tag_1 = factories.TagFactory(uri='tag_1')
        tag_2 = factories.TagFactory(uri='tag_2')
        tag_3 = factories.TagFactory(uri='tag_3')

        # When creating a new article.
        article = factories.ArticleFactory(tags=[tag_2, tag_1, tag_3])
        assert article.tags == [tag_1, tag_2, tag_3]

        # When assigning new tags.
        article.tags = [tag_3, tag_2, tag_1]
        assert article.tags == [tag_1, tag_2, tag_3]

        # When adding new tags.
        tag_0 = factories.TagFactory(uri='tag_0')
        tag_4 = factories.TagFactory(uri='tag_4')

        article.tags.add(tag_0)
        article.tags.add(tag_4)

        assert article.tags == [tag_0, tag_1, tag_2, tag_3, tag_4]

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
    doc_type = 'category'
    table = 'categories'


class TestTagModel(BaseTestModel):
    factory = factories.TagFactory
    model = models.Tag
    doc_type = 'tag'
    table = 'tags'

import pytest

from website import factories, models

from tests.base._test_models import BaseTestModel  # noqa: I100


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

    def test_sort_tags(self):
        tag_1 = factories.TagFactory(uri='abc')
        tag_2 = factories.TagFactory(uri='xyz')
        assert tag_1 < tag_2

    def test_sort_tag_with_other_object(self):
        tag = factories.TagFactory()

        with pytest.raises(AssertionError):
            assert tag < None

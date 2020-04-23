import pytest

from website import factories, models
from website.testing.models import BaseModelTest


class TestCategoryModel(BaseModelTest):
    factory = factories.CategoryFactory
    model = models.Category
    doc_type = 'category'
    table = 'categories'


class TestTagModel(BaseModelTest):
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

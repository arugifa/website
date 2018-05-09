from datetime import date
import re

import pytest

from website.exceptions import MultipleResultsFound


@pytest.mark.usefixtures('db')
class BaseTestModel:
    #: Model factory.
    factory = None
    #: Model class.
    model = None
    #: List of optional model's fields, if any.
    optional_fields = None
    #: Model's column which can be filtered (string type).
    filterable_column = None

    def test_table_name_is_model_name_in_plural(self):
        model_name = self.model.__name__

        if model_name.endswith('y'):
            model_name_plural = "{}ies".format(model_name[:-1])
        else:
            model_name_plural = "{}s".format(model_name)

        table_name = self.model.__tablename__

        expected = re.sub('(?!^)([A-Z]+)', r'_\1', model_name_plural).lower()
        assert table_name == expected

    def test_optional_fields_do_not_have_to_bet_defined(self):
        if self.optional_fields is None:
            pytest.skip("This model doesn't have optional fields")

        optional = {f: None for f in self.optional_fields}
        self.factory(**optional)  # Should not raise

    # Retrieve All Items

    def test_retrieve_all_items(self):
        items = self.factory.create_batch(2)
        assert self.model.all() == items

    # Retrieve One Item

    def test_find_one_item(self):
        self.factory(**{self.filterable_column: 'something'})
        expected = self.factory(**{self.filterable_column: 'another'})

        actual = self.model.find(**{self.filterable_column: 'another'})

        assert actual == expected

    def test_find_unexisting_item(self):
        assert self.model.find(**{self.filterable_column: 'nothing'}) is None

    def test_finding_similar_items_raises_an_exception(self):
        self.factory.create_batch(2, **{self.filterable_column: 'something'})

        with pytest.raises(MultipleResultsFound):
            self.model.find(**{self.filterable_column: 'something'})


class BaseTestDocumentModel(BaseTestModel):
    optional_fields = ['last_update', 'publication_date']
    filterable_column = 'title'

    def test_default_publication_date(self):
        document = self.factory(publication_date=None)
        assert document.publication_date == date.today()


class BaseTestRecommendedModel(BaseTestModel):
    filterable_column = 'title'

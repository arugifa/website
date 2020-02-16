"""Base classes to test models."""

from datetime import date
from typing import ClassVar

import pytest

from website import exceptions
from website.base.factories import BaseDatabaseFactory
from website.base.models import BaseModel
from website.factories import TagFactory


@pytest.mark.usefixtures('db')
class BaseTestModel:
    """Base class for all model tests."""

    #: Model factory.
    factory: ClassVar[BaseDatabaseFactory] = None
    #: Model class.
    model: ClassVar[BaseModel] = None
    #: Model's name.
    doc_type: ClassVar[str] = None
    #: Model's name in database (i.e., table's name).
    table: ClassVar[str] = None

    @pytest.fixture(scope='class')
    def filterable_column(self):
        filterable = filter(
            lambda c: (c.type.python_type is str) and not c.unique,
            self.model.__table__.columns.values(),
        )

        try:
            return next(filterable)
        except StopIteration:
            error = (
                f"Cannot use {BaseTestModel.__name__} "
                f"for testing {self.model.__name__}"
            )
            raise RuntimeError(error)

    @pytest.fixture(scope='class')
    def feed(self, filterable_column):
        return {filterable_column.name: 'to_keep'}

    @pytest.fixture(scope='class')
    def residue(self, filterable_column):
        return {filterable_column.name: 'to_keep'}

    @pytest.fixture(scope='class')
    def filtrate(self, filterable_column):
        return {filterable_column.name: 'to_drop'}

    # General.

    def test_table_name_is_model_name_in_plural(self):
        assert self.model.__tablename__ == self.table

    def test_document_type_is_valid(self):
        item = self.factory.build()
        assert item.doc_type == self.doc_type

    def test_mandatory_fields_must_be_defined(self, db):
        def is_mandatory(field):
            if field.nullable:
                return False

            if field.primary_key and field.type.python_type is int:
                if field.autoincrement == 'auto':
                    return False

            return True

        mandatory_fields = [
            c.name for c in self.model.__table__.columns.values() if is_mandatory(c)
        ]

        if not mandatory_fields:
            pytest.skip("This model doesn't have optional fields")

        for field in mandatory_fields:
            item = self.factory.build(**{field: None})

            with pytest.raises(exceptions.InvalidItem):
                item.save()

            # XXX: Could maybe use pytest.mark.parametrize instead (03/2019)
            # If the following proposal gets implemented:
            # https://github.com/pytest-dev/pytest/issues/349
            # In which case, mandatory and optional fields could be defined
            # inside fixtures. So we don't have to rollback manually the db
            # (already done during teardown in the db fixture after each test).
            db.session.rollback()

    def test_optional_fields_do_not_have_to_bet_defined(self):
        optional_fields = [
            c.name for c in self.model.__table__.columns.values() if c.nullable
        ]

        if not optional_fields:
            pytest.skip("This model doesn't have optional fields")

        optional = {f: None for f in optional_fields}
        self.factory(**optional)  # Should not raise

    # Retrieve all items.

    def test_retrieve_all_items(self):
        items = self.factory.create_batch(2)
        assert self.model.all() == items

    # Filter items.

    def test_filter_items(self, feed, filtrate, residue):
        self.factory(**filtrate)
        expected = self.factory.create_batch(2, **residue)
        actual = self.model.filter(**feed)
        assert actual == expected

    # Retrieve one item.

    def test_find_one_item(self, filtrate, residue):
        self.factory(**filtrate)
        expected = self.factory(**residue)
        actual = self.model.find(**residue)
        assert actual == expected

    def test_find_not_existing_item(self, residue):
        with pytest.raises(exceptions.ItemNotFound):
            self.model.find(**residue)

    def test_finding_similar_items_raises_an_exception(self, residue):
        self.factory.create_batch(2, **residue)

        with pytest.raises(exceptions.MultipleItemsFound):
            self.model.find(**residue)

    # Check if item exists.

    def test_item_exists(self):
        item = self.factory()
        assert item.exists() is True

    def test_item_does_not_exist(self):
        item = self.factory.build()
        assert item.exists() is False

    # Delete an item.

    def test_delete_item(self):
        item = self.factory()
        assert item.exists() is True

        item.delete()
        assert item.exists() is False

    # Save an item.

    def test_save_item(self):
        item = self.factory()
        assert item.exists() is True

    def test_save_invalid_item(self):
        item = self.factory.build(uri={'invalid': 'attribute'})

        with pytest.raises(exceptions.InvalidItem):
            item.save()

    # Update an item.

    def test_update_item(self):
        item = self.factory(uri='123')
        assert item.uri == '123'

        item.update(uri='456')
        assert item.uri == '456'

    def test_update_item_with_invalid_attributes(self):
        item = self.factory()

        with pytest.raises(exceptions.InvalidItem):
            item.update(uri={'invalid': 'attribute'})


class BaseTestDocumentModel(BaseTestModel):

    # Publication date.

    def test_default_publication_date(self):
        document = self.factory(publication_date=None)
        assert document.publication_date == date.today()

    # Last update.

    def test_last_update_is_set_automatically_when_changes_are_made(self):
        document = self.factory()
        assert document.last_update is None

        document.uri = 'new_uri'
        document.save()
        assert document.last_update == date.today()

    # Tags.

    def test_tag_list_is_always_sorted(self):
        tag_1 = TagFactory(uri='tag_1')
        tag_2 = TagFactory(uri='tag_2')
        tag_3 = TagFactory(uri='tag_3')

        # When creating a new article.
        document = self.factory(tags=[tag_2, tag_1, tag_3])
        assert document.tags == [tag_1, tag_2, tag_3]

        # When assigning new tags.
        document.tags = [tag_3, tag_2, tag_1]
        assert document.tags == [tag_1, tag_2, tag_3]

        # When adding new tags.
        tag_0 = TagFactory(uri='tag_0')
        tag_4 = TagFactory(uri='tag_4')

        document.tags.add(tag_0)
        document.tags.add(tag_4)

        assert document.tags == [tag_0, tag_1, tag_2, tag_3, tag_4]

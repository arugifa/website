import pytest
from pytest_bdd import given, then, scenario, when
from pytest_bdd.parsers import parse

from website.factories import LifeNoteFactory


# Scenarios

@pytest.mark.skip(reason="Feature not yet fully implemented")
@scenario('features/life_notes.feature', "Navigate to life notes")
def test_navigate_to_life_notes():
    pass


# Requirements

@given(parse("I wrote {count:d} life notes"))
def life_notes(db, count):
    return LifeNoteFactory.create_batch(count)


# Actions

@when("I go to my life notes")
def go_to_life_notes(browser):
    life_notes = browser.find_link_by_text("Life Notes")[0]
    browser.visit(life_notes)


# Assertions

@then(parse("I should see {count:d} life notes"))
def life_notes_displayed(browser, count):
    pass


@then("they should be sorted chronologically in descending order")
def sorted_in_descending_order(browser):
    pass

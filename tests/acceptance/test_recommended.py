import pytest
from pytest_bdd import given, scenario, then, when
from pytest_bdd.parsers import parse

from website.factories import RecommendedArticleFactory


# Scenarios

@pytest.mark.skip(reason="Feature not yet implemented")
@scenario('features/recommended.feature', "Navigate to recommended material")
def test_navigate_to_recommended_reading():
    pass


# Requirements

@given(parse("I read and recommend {count:d} articles"))
def recommended_articles(db, count):
    return RecommendedArticleFactory.create_batch(count)


# Actions

@when("I go to my recommended material")
def go_to_recommended_reading(browser):
    reading = browser.find_link_by_text("Recommended Material")[0]
    browser.visit(reading)


# Assertions

@then(parse("I should see {count:d} recommended articles"))
def recommended_articles_displayed(browser, count):
    pass


@then("they should be sorted chronologically in descending order")
def sorted_in_descending_order(browser):
    pass

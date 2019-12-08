from pytest_bdd import given, scenario, then, when
from pytest_bdd.parsers import re as parse_regex

from website.blog.test import create_articles


# Scenarios

@scenario('features/blog.feature', "Navigate to blog articles")
def test_navigate_to_blog_articles():
    pass


@scenario('features/blog.feature', "Read a blog article")
def test_read_blog_article():
    pass


# Requirements

@given(parse_regex(r"I wrote (?P<count>\d+) blog articles?"))
def articles(db, count):
    return create_articles(int(count))


# Actions

@when("I go to my article")
def go_to_article(browser):
    article = browser.find_by_css('.article-list__title').first
    article.click()


# Assertions

@then("I should see its content")
def article_is_displayed(browser, articles):
    # We are reading the most recent article, which is also the last one created.
    article = articles[-1]

    assert browser.is_text_present(article.title)

    # Cannot use .is_text_present() to check if the article's content is present,
    # as this method strips all HTML tags before performing the verification.
    assert article.body in browser.find_by_css('.article')[0].html


@then("I should see all articles")
def articles_are_displayed(browser, articles):
    displayed_articles = browser.find_by_css('.article-list__title')
    assert len(displayed_articles) == len(articles)


@then("they should be sorted chronologically in descending order")
def articles_are_sorted_in_descending_order(browser, articles):
    actual = [article.text for article in browser.find_by_css('.article-list__title')]
    expected = [article.title for article in articles[::-1]]
    assert actual == expected

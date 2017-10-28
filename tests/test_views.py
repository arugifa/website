from datetime import date, timedelta
from operator import attrgetter

from website import factories


def find_links(page, class_name):
    css_selector = 'a.%s' % class_name
    return [link['href'] for link in page.html.select(css_selector)]


def test_home_page(client, db):
    # Blog articles should be sorted by publication date
    # on the home page. We already check that in acceptance tests.
    # However, we try to cover here more edge cases,
    # in order to keep acceptance tests short and simple.

    today = date.today()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(weeks=1)

    # Hence, we first create articles unordered.
    # By doing that, we can be sure that articles will not
    # be sorted by primary key in ascending order.
    articles = [
        factories.ArticleFactory(publication=pub_date)
        for pub_date in [yesterday, last_week, today]]

    response = client.get('/')
    actual = find_links(response, 'article-list__title')

    # To finally check that they are sorted in descending chronological order.
    expected = [
        '/articles/%s.html' % article.uri for article
        in sorted(articles, key=attrgetter('publication'), reverse=True)]

    assert actual == expected


class TestArticleView:
    def test_retrieve_article(self, client, db):
        article = factories.ArticleFactory()

        response = client.get('/articles/%s.html' % article.uri)

        assert article.title in response.html.title.text
        # Use .decode() instead of .text to keep HTML tags.
        assert article.content in response.html.body.decode()

        # Last update date is not displayed when not defined.
        update_date = response.html.select_one('.article__update')
        assert article.last_update is update_date is None

    def test_retrieve_unexisting_article(self, client, db):
        client.get('/articles/dont_exist.html', status=404)  # Should not raise

    def test_with_different_publication_and_update_dates(self, client, db):
        """Check that both dates are displayed."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        article = factories.ArticleFactory(
            publication=yesterday, last_update=today)

        response = client.get('/articles/%s.html' % article.uri)
        publication = response.html.select('.article__publication')
        update = response.html.select('.article__update')

        assert publication != update

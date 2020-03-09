from datetime import date, timedelta
from operator import attrgetter

from arugifa.website.blog import factories


class TestBlogHomeView:
    def find_links(self, page, class_name):
        css_selector = 'a.%s' % class_name
        return [link['href'] for link in page.html.select(css_selector)]

    def test_articles_are_sorted_by_publication_date(self, client, db):
        """We already check this in acceptance tests.

        However, we try to cover here more edge cases, in order to keep acceptance
        tests short and simple.
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(weeks=1)

        # Hence, we first create articles unordered.
        # By doing that, we can be sure that articles will not be sorted by primary key
        # in ascending order.
        articles = [
            factories.ArticleFactory(publication_date=pub_date)
            for pub_date in [yesterday, last_week, today]
        ]

        response = client.get('/')
        actual = self.find_links(response, 'article-list__title')

        # To finally check that they are sorted in descending chronological order.
        expected = [
            '/articles/%s.html' % article.uri for article
            in sorted(articles, key=attrgetter('publication_date'), reverse=True)
        ]

        assert actual == expected


class TestArticleView:
    def test_retrieve_article(self, client, db):
        article = factories.ArticleFactory()

        response = client.get('/articles/%s.html' % article.uri)

        assert article.title in response.html.title.text
        # Use .decode() instead of .text to keep HTML tags.
        assert article.body in response.html.body.decode()

        # Last update date is not displayed when not defined.
        update_date = response.html.select_one('.article__update')
        assert article.last_update is update_date is None

    def test_retrieve_unexisting_article(self, client, db):
        client.get('/articles/dont_exist.html', status=404)  # Should not raise

    def test_publication_and_update_dates_are_both_displayed(self, client, db):
        today = date.today()
        yesterday = today - timedelta(days=1)
        article = factories.ArticleFactory(
            publication_date=yesterday, last_update=today)

        response = client.get('/articles/%s.html' % article.uri)
        publication = response.html.select('.article__publication')
        update = response.html.select('.article__update')

        assert publication != update

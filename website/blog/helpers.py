from datetime import date, timedelta

from .factories import ArticleFactory


def create_articles(count):
    """Create blog articles, with different publication dates.

    Articles are sorted by publication date, in ascending order.

    :param int count: number of articles to create.
    """
    today = date.today()
    return [
        ArticleFactory(publication_date=today - timedelta(days=days))
        for days in range(count, 0, -1)]

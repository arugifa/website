"""Collection of helper functions."""

from datetime import date, timedelta
from typing import List

from website.blog.factories import ArticleFactory
from website.blog.models import Article


def create_articles(count: int) -> List[Article]:
    """Create blog articles, with different publication dates.

    Articles are sorted by publication date, in ascending order.

    :param count: number of articles to create.
    """
    today = date.today()
    return [
        ArticleFactory(publication_date=today - timedelta(days=days))
        for days in range(count, 0, -1)]

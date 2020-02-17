"""Blog file handlers."""

from website.base.handlers import BaseDocumentFileHandler
from website.blog.models import Article
from website.blog.processors import ArticleFileProcessor


class ArticleFileHandler(BaseDocumentFileHandler):
    """Manage the life cycle of a blog article in database.

    Inside its repository, the article's source file must be organized by year,
    and then classified by month and day, as follows:
    ``blog/<YEAR>/<MONTH>-<DAY>.<URI>.<EXTENSION>``
    """

    model = Article
    processor = ArticleFileProcessor

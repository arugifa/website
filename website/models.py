"""Global website models."""

from website import db
from website.base.models import BaseMetadataModel


class Category(BaseMetadataModel):
    """Article category (e.g., programming, mountaineering, politics, etc)."""

    articles = db.relationship('Article', back_populates='category')


class Tag(BaseMetadataModel):
    """Article tag (e.g., Python, cloud, Rust, etc.)."""

    articles = db.relationship(
        'Article', secondary='article_tags', back_populates='_tags')

    def __lt__(self, other):
        assert isinstance(other, Tag)
        return self.uri < other.uri

    # TODO: write test in content update manager (03/2019)
    # @classmethod
    # def delete_orphans(cls) -> int:
    #     """Delete tags not associated with any other documents.

    #     :return: number of tags deleted.
    #     """
    #     # Thanks to https://stackoverflow.com/a/18193592/2987526
    #     from sqlalchemy import func
    #     return db.session.query(Tag).having(func.count(Article.id) == 0).delete()  # noqa: E501


# For relationships to work properly.
from website.blog.models import Article  # noqa: E402, F401, I202

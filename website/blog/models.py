"""Blog models."""

from operator import attrgetter
from typing import Iterable, Iterator

from sortedcontainers import SortedKeyList
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property

from website import db
from website.models import BaseModel, Document


# Custom Types

class TagList(SortedKeyList):
    """Keep tags always sorted.

    This makes testing easier, especially when documents are updated
    and that tags are inserted asynchronously.
    """

    def __init__(self, tags: Iterable['Tag'] = None):
        SortedKeyList.__init__(self, tags, key=attrgetter('uri'))

    def append(self, tag: 'Tag'):  # noqa: D401
        """Method required by SQLAlchemy.

        In order to populate the list when loading tags from database.
        """
        return self.add(tag)


# Models

class Article(Document):
    """Blog article."""

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    title = db.Column(db.String, nullable=False)
    lead = db.Column(db.String, nullable=False)
    body = db.Column(db.Text, nullable=False)

    category = db.relationship('Category', back_populates='articles')
    _tags = db.relationship(
        'Tag', order_by='Tag.uri', collection_class=TagList,
        secondary='article_tags', back_populates='articles')

    @hybrid_property
    def tags(self) -> TagList:
        """Return sorted tags."""
        return self._tags

    @tags.setter
    def tags(self, value: Iterable):
        """Sort tags when overwriting them."""
        self._tags = TagList(value)

    @classmethod
    def latest_ones(cls) -> Iterator['Article']:
        """Return articles ordered by publication date, in descending order.

        More precisely, articles are sorted by:

        - publication date in descending order first,
        - primary key in ascending order then.
        """
        return cls.query.order_by(cls.publication_date.desc(), cls.id.desc())


class Category(BaseModel):
    """Article category (e.g., programming, mountaineering, politics, etc)."""

    name = db.Column(db.String, nullable=False)
    articles = db.relationship('Article', back_populates='category')


class Tag(BaseModel):
    """Article tag (e.g., Python, cloud, Rust, etc.)."""

    name = db.Column(db.String, nullable=False)
    articles = db.relationship(
        'Article', secondary='article_tags', back_populates='_tags')


# Many-to-Many Relationships

tags = db.Table(
    'article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
)

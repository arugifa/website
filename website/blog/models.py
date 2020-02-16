"""Blog's database models."""

from datetime import date
from typing import Iterator

from website import db
from website.base.models import BaseDocument, TagList


# Models

class Article(BaseDocument):
    """Blog article."""

    title = db.Column(db.String, nullable=False)
    lead = db.Column(db.String, nullable=False)
    body = db.Column(db.Text, nullable=False)

    publication_date = db.Column(db.Date, default=date.today, nullable=False)
    last_update = db.Column(db.Date, onupdate=date.today)

    category = db.relationship('Category', back_populates='articles')
    # TODO: Use @declared_attr on BaseDocument to be DRY (02/2020)
    _tags = db.relationship(
        'Tag', order_by='Tag.uri', collection_class=TagList,
        secondary='article_tags', back_populates='articles')

    @classmethod
    def latest_ones(cls) -> Iterator['Article']:
        """Return articles ordered by publication date, in descending order.

        More precisely, articles are sorted by:

        - publication date in descending order first,
        - primary key in ascending order then.
        """
        return cls.query.order_by(cls.publication_date.desc(), cls.id.desc())


# Many-to-Many Relationships

tags = db.Table(
    'article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
)

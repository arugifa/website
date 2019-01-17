"""Blog models."""

from datetime import date
from typing import Generator

from website import db
from website.models import BaseModel, Document


# Models

class Article(Document):
    """Blog article."""

    # TODO: Use declared attribute for table names, in the base class (01/2019)
    # For example:
    #     @declared_attr
    #     def __tablename__(cls):
    #         return cls.__name__.lower()
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    uri = db.Column(db.String, unique=True, nullable=False)

    title = db.Column(db.String, nullable=False)
    introduction = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)

    publication_date = db.Column(db.Date, default=date.today, nullable=False)
    last_update = db.Column(db.Date)

    category = db.Relationship('Category', back_populates='articles')
    tags = db.relationship('Tag', secondary='tags', back_populates='articles')

    @classmethod
    def latest_ones(cls) -> Generator['Article']:
        """Return articles ordered by publication date, in descending order.

        More precisely, articles are sorted by:

        - publication date in descending order first,
        - primary key in ascending order then.
        """
        return cls.query.order_by(cls.publication_date.desc(), cls.id.desc())


class Category(BaseModel):
    """Article category (e.g., programming, mountaineering, politics, etc)."""

    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)

    uri = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    articles = db.relationship('Article', back_populates='category')


class Tag(BaseModel):
    """Article tag (e.g., Python, cloud, Rust, etc.)."""

    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)

    uri = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    articles = db.Relationship('Article', secondary='tags', back_populates='tags')  # noqa: E501


# Many-to-Many Relationships

tags = db.Table(
    'article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
)

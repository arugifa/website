"""Blog models."""

from typing import Iterator

from sqlalchemy import func

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

    title = db.Column(db.String, nullable=False)
    lead = db.Column(db.String, nullable=False)
    body = db.Column(db.Text, nullable=False)

    category = db.relationship('Category', back_populates='articles')
    tags = db.relationship(
        'Tag', order_by='Tag.uri',
        secondary='article_tags', back_populates='articles')

    @classmethod
    def latest_ones(cls) -> Iterator['Article']:
        """Return articles ordered by publication date, in descending order.

        More precisely, articles are sorted by:

        - publication date in descending order first,
        - primary key in ascending order then.
        """
        return cls.query.order_by(cls.publication_date.desc(), cls.id.desc())

    def exists(self) -> bool:
        """Check if an article with the same :attr:`uri` already exists."""
        # Thx to https://stackoverflow.com/a/41951905/2987526
        article = Article.query.filter_by(uri=self.uri)
        return db.session.query(article.exists()).scalar()


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
    articles = db.relationship('Article', secondary='article_tags', back_populates='tags')  # noqa: E501

    @classmethod
    def delete_orphans(cls) -> int:
        """Delete tags not associated with any other documents.

        :return: number of tags deleted.
        """
        # Thanks to https://stackoverflow.com/a/18193592/2987526
        return db.session.query(Tag).having(func.count(Article.id) == 0).delete()


# Many-to-Many Relationships

tags = db.Table(
    'article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
)

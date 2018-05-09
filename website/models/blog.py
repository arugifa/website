from website import db

from .base import BaseModel
from .documents import Document


tags = db.Table(
    'article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
)


class Category(BaseModel):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)

    articles = db.relationship('Article', backref='category')

    name = db.Column(db.String, nullable=False)
    uri = db.Column(db.String, unique=True, nullable=False)


class Article(Document):
    __tablename__ = 'articles'

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    tags = db.relationship('Tag', secondary=tags, backref='articles')

    teaser = db.Column(db.String, nullable=False)

    @classmethod
    def latest(cls):
        """Return articles ordered by publication date, in descending order.

        More precisely, articles are sorted by:

        - publication date in descending order first,
        - primary key in ascending order then.

        :rtype: generator
        """
        return cls.query.order_by(cls.publication_date.desc(), cls.id.desc())
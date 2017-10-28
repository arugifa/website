from datetime import date

from flask_sqlalchemy import SQLAlchemy
import sqlalchemy

db = SQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True

    @classmethod
    def all(cls):
        return cls.query.all()


# Exceptions

class MultipleResultsFound(Exception):
    pass


# Documents

class Document(BaseModel):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    publication = db.Column(db.Date, default=date.today, nullable=False)
    last_update = db.Column(db.Date)
    source = db.Column(db.Text, nullable=False)
    uri = db.Column(db.String, unique=True, nullable=False)

    @classmethod
    def all(cls):
        return cls.query.all()


class Article(Document):
    __tablename__ = 'articles'

    teaser = db.Column(db.String, nullable=False)

    @classmethod
    def find(cls, **kwargs):
        """Search for a unique article.

        Search parameters should be given as keyword arguments.

        :rtype: a :class:`.Article` instance if found; ``None`` otherwise.
        :raise: :class:`.MultipleResultsFound` if several articles are found.
        """
        try:
            return cls.query.filter_by(**kwargs).one_or_none()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            raise MultipleResultsFound

    @classmethod
    def latest(cls):
        """Return articles ordered by publication date, in descending order.

        More precisely, articles are sorted by:

        - publication date in descending order first,
        - primary key in ascending order then.

        :rtype: generator
        """
        return cls.query.order_by(cls.publication.desc(), cls.id.desc())


class LifeNote(Document):
    __tablename__ = 'life_notes'


# Recommended Material

class RecommendedMaterial(BaseModel):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    summary = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False)


class RecommendedArticle(RecommendedMaterial):
    __tablename__ = 'recommended_articles'


class RecommendedBook(RecommendedMaterial):
    __tablename__ = 'recommended_books'


class RecommendedVideo(RecommendedMaterial):
    __tablename__ = 'recommended_videos'

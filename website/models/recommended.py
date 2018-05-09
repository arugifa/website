from website import db

from .base import BaseModel


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

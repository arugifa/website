from datetime import date

from website import db

from .base import BaseModel


class Document(BaseModel):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    publication_date = db.Column(db.Date, default=date.today, nullable=False)
    last_update = db.Column(db.Date)
    uri = db.Column(db.String, unique=True, nullable=False)


class Tag(BaseModel):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False)
    uri = db.Column(db.String, unique=True, nullable=False)

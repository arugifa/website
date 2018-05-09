from website import db

from .documents import Document


tags = db.Table(
    'note_tags',
    db.Column('note_id', db.Integer, db.ForeignKey('notes.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
)


class Note(Document):
    __tablename__ = 'notes'

    tags = db.relationship('Tag', secondary=tags, backref='notes')
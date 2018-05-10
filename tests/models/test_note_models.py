from website.notes import factories, models
from website.test.models import BaseTestDocumentModel


class TestNoteModel(BaseTestDocumentModel):
    factory = factories.NoteFactory
    model = models.Note

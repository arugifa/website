from website.factories import notes as factories
from website.models import notes as models
from website.test.models import BaseTestDocumentModel


class TestNoteModel(BaseTestDocumentModel):
    factory = factories.NoteFactory
    model = models.Note

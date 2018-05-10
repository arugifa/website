from factory import List, Sequence, SubFactory

from website.factories import DocumentFactory, TagFactory

from . import models


class NoteFactory(DocumentFactory):
    class Meta:
        model = models.Note

    title = Sequence(lambda n: f"Life Note {n}")
    content = "<p>This is the life note's content.</p>"
    tags = List([SubFactory(TagFactory) for _ in range(2)])
    uri = Sequence(lambda n: f'lifenote_{n}')

from datetime import date

from factory import LazyFunction, Sequence
from factory.alchemy import SQLAlchemyModelFactory

from . import models


class BaseSQLAlchemyFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = models.db.session

        # We commit the session after fixtures creation.
        # It's especially important when launching for example
        # a shell in parallel of the demo server. If the session is not
        # committed, it's impossible to access to initial data from the shell.
        sqlalchemy_session_persistence = 'commit'


# Documents

class DocumentFactory(BaseSQLAlchemyFactory):
    class Meta:
        abstract = True

    publication = LazyFunction(date.today)
    last_update = None


class ArticleFactory(DocumentFactory):
    class Meta:
        model = models. Article

    title = Sequence(lambda n: "Article %d" % n)
    teaser = "This is the article's teaser."
    content = "<p>This is the article's content.</p>"
    source = "This is the article's content."
    uri = Sequence(lambda n: "article_%d" % n)


class LifeNoteFactory(DocumentFactory):
    class Meta:
        model = models.LifeNote

    title = Sequence(lambda n: "Life Note %d" % n)
    content = "<p>This is the life note's content.</p>"
    source = "This is the life note's content."
    uri = Sequence(lambda n: "lifenote_%d" % n)


# Recommended Material

class RecommendedArticleFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.RecommendedArticle

    title = Sequence(lambda n: "Recommended Article %d" % n)
    summary = "This is a recommended article."
    url = Sequence(lambda n: "http://www.medium.com/%d" % n)


class RecommendedBookFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.RecommendedBook

    title = Sequence(lambda n: "Recommended Book %d" % n)
    summary = "This is a recommended video."
    url = Sequence(lambda n: "http://www.oreilly.com/%d" % n)


class RecommendedVideoFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.RecommendedVideo

    title = Sequence(lambda n: "Recommended Video %d" % n)
    summary = "This is a recommended video."
    url = Sequence(lambda n: "http://www.youtube.com/%d" % n)

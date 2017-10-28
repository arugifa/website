from . import factories
from .helpers import create_articles
from .models import db


def setup_demo(app, item_count=10):
    with app.app_context():
        db.drop_all()  # Ensure a clean state in case database already exists
        db.create_all()

        create_articles(item_count)
        factories.LifeNoteFactory.create_batch(item_count)
        factories.RecommendedArticleFactory.create_batch(item_count)

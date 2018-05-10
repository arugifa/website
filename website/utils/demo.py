from website.blog.helpers import create_articles


def setup_demo(app, item_count=10):
    with app.app_context():
        create_articles(item_count)

from arugifa.website import demo
from arugifa.website.blog import factories, models


class TestSetupDemo:
    def test_database_precleanup(self, app, db):
        article = factories.ArticleFactory()
        assert models.Article.all() == [article]

        demo.setup_demo(app)
        assert article not in models.Article.all()

    def test_database_state(self, app, db):
        demo.setup_demo(app, item_count=5)
        assert len(models.Article.all()) == 5

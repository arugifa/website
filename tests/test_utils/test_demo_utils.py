from website import factories, models, utils


class TestSetupDemo:
    def test_database_precleanup(self, app, db):
        article = factories.ArticleFactory()
        assert models.Article.all() == [article]

        utils.setup_demo(app)
        assert article not in models.Article.all()

    def test_database_state(self, app, db):
        utils.setup_demo(app, item_count=5)

        assert len(models.Article.all()) == 5
        assert len(models.LifeNote.all()) == 5
        assert len(models.RecommendedArticle.all()) == 5

from website.blog import helpers


def test_create_articles(db):
    articles = helpers.create_articles(3)

    assert len(articles) == 3

    # As in real life, recently written articles should have
    # a publication date/primary key more recent/higher
    # than older ones.

    assert articles[0].publication < \
           articles[1].publication < \
           articles[2].publication

    assert articles[0].id < articles[1].id < articles[2].id

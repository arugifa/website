from website.blog.helpers import create_articles
from website.test import TEST_CONTAINER_PREFIX


def retrieve_test_containers(connection):
    # TODO: add test
    test_containers = filter(
        lambda c: c.name.startswith(TEST_CONTAINER_PREFIX),
        connection.object_store.containers())

    return list(test_containers)


def setup_demo(app, item_count=10):
    with app.app_context():
        create_articles(item_count)

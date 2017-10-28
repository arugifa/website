from . import TEST_CONTAINERS_PREFIX


def retrieve_test_containers(connection):
    # TODO: add test
    test_containers = filter(
        lambda c: c.name.startswith(TEST_CONTAINERS_PREFIX),
        connection.object_store.containers())

    return list(test_containers)

import logging
from collections.abc import MutableMapping as AbstractMutableMapping
from pathlib import Path
from typing import Callable

from website.compat import Container as _Container

logger = logging.getLogger(__name__)


class Container(_Container):
    @property
    def objects(self) -> 'ObjectCollection':
        return ObjectCollection(self._connection, self)


class ObjectCollection(AbstractMutableMapping):
    def __init__(self, connection: Callable, container: Container):
        self.connection = connection
        self.object_store = connection.object_store
        self.container = container

    def __delitem__(self, key):
        self.object_store.delete_object(key)

    def __getitem__(self, key):
        """...

        :raise openstack.exceptions.ResourceNotFound: ...
        """
        return self.connection.object_store.get_object_metadata(key, self.container)

    def __iter__(self):
        return iter(o.name for o in self.object_store.objects(self.container))

    def __len__(self):
        return len(self.object_store.objects(self.container))

    def __setitem__(self, key: str, value: Path):
        try:
            data = value.open('rb').read()

            # TODO: Can be shortened, after upgrade of OpenStackSDK to 0.10+:
            #  object_store.upload_object(self.container, key, **value)
            self.object_store.upload_object(container=self.container, name=key, data=data)
        except OSError as exc:
            logger.error("Couldn't read content of %s: %s", key, exc)

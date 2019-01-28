"""Util functions to be used for making scripts.

They all contain side effects and are not tested!
"""
import logging
from hashlib import md5
from pathlib import Path
from typing import BinaryIO, Callable, Generator, Iterable, List, Mapping, TextIO

from openstack.exceptions import ResourceNotFound, SDKException
from rackspace.connection import Connection

from website.openstack import Container

logger = logging.getLogger(__name__)


class CloudManager:
    """...

    https://docs.openstack.org/openstacksdk/latest/user/proxies/object_store.html
    """  # noqa: E501
    def __init__(
            self, user: str, api_key: str, region: str, container: str,
            cls: Callable = Connection):
        try:
            self._connection = cls(username=user, api_key=api_key, region=region)
            self._object_store = self._connection.object_store
            self._container = self.object_store.get_container_metadata(container)
        except ResourceNotFound:
            raise KeyError(key)
        except SDKException as exc:
            logger.error("Cannot connect to the Cloud: %s", exc)
            raise CloudConnectionError(str(exc))

        self.container = Container.existing(connection=self._connection, **_container._attrs)

    def update(self, src: Path) -> None:
        local_files = set(str(path.relative_to(src)) for path in src.rglob('*') if path.is_file())
        # set(obj.name for obj in self.object_store.objects(self.container))
        remote_files = set(obj.name for obj in self.container.objects)

        # Update remote files.
        to_delete = list(remote_files - local_files)
        to_add = {path: src / path for path in local_files - remote_files}
        to_compare = {path: src / path for path in local_files - set(to_add)}

        self._add(to_add) if to_add else logger.info("No new file to upload")
        self._update(to_compare)
        self._delete(to_delete) if to_delete else logger.info("No remote file to delete")

    def upload(self, src: Path, dst: str) -> Callable:
        # TODO: Read file chunk by chunk, to not overfit memory.
        try:
            # TODO: Can be shortened, after upgrade of OpenStackSDK to 0.10+:
            #  object_store.upload_object(self.container, str(path), data=content)
            # return self.object_store.upload_object(container=self.container, name=dst, data=data)
            self.container[dst] = src
        except SDKException as exc:
            logger.error("Couldn't upload %s: %s", src, exc)
        else:
            logger.info("%s uploaded", src)

        return self.container[dst]

    # Helpers

    @staticmethod
    def _md5sum(src: Path) -> str:
        md5sum = md5()

        with src.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5sum.update(chunk)

        return md5sum.hexdigest()

    def _add(self, local_files: Mapping[str, Path]) -> List[Callable]:
        added = []

        logger.info("Uploading new files...")
        for dst, src in sorted(local_files.items()):
            obj = self.upload(src, dst)
            added.add(obj)

        return added

    def _delete(self, remote_files: Iterable[str]) -> None:
        logger.info("Deleting outdated remote files...")

        for path in sorted(remote_files):
            try:
                # self.object_store.delete_object(path, container=container)
                del self.container[path]
            except SDKException as exc:
                logger.error("Couldn't delete %s: %s", path, exc)
            else:
                logger.info("%s deleted", path)

    def _update(self, remote_files: Mapping[str, Path]) -> List[Callable]:
        logger.info("Comparing existing files...")
        updated = []

        for dst, src in sorted(remote_files.items()):
            local_hash = self._md5sum(src)
            # remote_hash = self.object_store.get_object_metadata(dst, self.container).etag
            remote_hash = self.container.objects[dst].etag

            if local_hash != remote_hash:
                obj = self.upload(src, dst)
                updated.add(obj)

        if not updated:
            logger.info("No remote file to update")

        return updated

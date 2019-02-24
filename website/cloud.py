"""Util functions to be used for making scripts.

They all contain side effects and are not tested!
"""
import logging
from hashlib import md5
from pathlib import Path
from typing import (
    BinaryIO, Callable, Dict, Generator, Iterable, List, Mapping, TextIO, Union)

import openstack
from openstack.exceptions import ResourceNotFound, SDKException
from openstack.object_store.v1.obj import Object

from website import exceptions
from website.openstack import Container
from website.stubs import CloudStubObject

logger = logging.getLogger(__name__)


class CloudManager:
    """...

    https://docs.openstack.org/openstacksdk/latest/user/proxies/object_store.html
    """  # noqa: E501
    def __init__(self, local_dir: Path, container: str, factory: Callable = openstack.connect):
        try:
            connection = factory()
            self._object_store = connection.object_store
            _container = self.get_container(container)
        except SDKException as exc:
            raise exceptions.CloudConnectionFailure(exc)

        self.local_dir = local_dir
        self.container = Container.existing(
            connection=connection, **_container._attrs)

    def _get_container(self, name):
        try:
            return self._object_store.get_container_metadata(name)
        except ResourceNotFound:
            return self._object_store.create_container(name)


    def update(self) -> Dict[str, List]:
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

    def upload(self, src: Path, dst: str) -> Union[Object, CloudStubObject]:
        try:
            self.container[dst] = src
        except SDKException as exc:
            raise exceptions.CloudUploadError(exc)

        return self.container[dst]

    # Helpers

    @staticmethod
    def md5sum(src: Path) -> str:
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

    def refresh(self, local_files: Iterable[Path]) -> List[Path]:
        refreshed = []

        for src in local_files:
            dst = src.relative_to(self.local_dir)

            local_hash = self.md5sum(src)
            remote_hash = self.container.objects[dst].etag

            if local_hash != remote_hash:
                obj = self.upload(src, dst)
                refreshed.append(obj)

        return refreshed

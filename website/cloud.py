import logging
from hashlib import md5
from pathlib import Path
from typing import BinaryIO, Callable, Dict, Iterable, List, Tuple, Union

import openstack
from openstack.connection import Connection
from openstack.exceptions import ResourceNotFound, SDKException
from openstack.object_store.v1.obj import Object

from website import exceptions
from website.stubs import CloudStubObject

logger = logging.getLogger(__name__)


def connect(factory: Callable = openstack.connect):
    try:
        return factory()
    except SDKException as exc:
        raise exceptions.CloudConnectionFailure(exc)


class CloudFilesManager:
    """...

    https://docs.openstack.org/openstacksdk/latest/user/proxies/object_store.html
    """  # noqa: E501
    def __init__(
            self,
            connection: Union[Connection, 'CloudStubConnection'],
            container: str):
        try:
            self.object_store = connection.object_store
            self.container = self.object_store.get_container_metadata(container)  # noqa: E501
        except ResourceNotFound:
            raise exceptions.CloudContainerNotFound(container)
        except SDKException as exc:
            raise exceptions.CloudError(exc)

    # Main API

    def update(self, static_files: Path) -> Dict[str, List]:
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

    def upload(self, src: Path, dst: str = None) -> Union[Object, CloudStubObject]:  # noqa: E501
        """Upload the content of a file located at ``src``.

        The file's path is used to name the file in the :attr:`container`.

        :param dst: optional new name/path to give to the file once uploaded.
        :raise OSError: if cannot open a file locally to read its content.
        :raise ~.CloudUploadError: if something wrong happens during upload.
        """
        dst = dst or str(src)

        with src.open('rb') as source:  # Can raise OSError
            data = source.read()

        try:
            return self.object_store.upload_object(self.container, dst, data=data)  # noqa: E501
        except SDKException as exc:
            raise exceptions.CloudUploadError(exc)

    def download(self, dst: str) -> BinaryIO:
        """Download a file named ``dst``.

        :raise ~.CloudFileNotFound:
            when trying to download a file which doesn't exist.
        :raise ~.CloudError:
            if something wrong happens during download.
        """
        try:
            return self.object_store.download_object(dst, self.container)
        except ResourceNotFound:
            raise exceptions.CloudFileNotFound(self.container.name, dst)
        except SDKException as exc:
            raise exceptions.CloudError(exc)

    # Helpers

    @staticmethod
    def md5sum(src: Path) -> str:
        """Compute MD5 hash of a file located at ``src``.

        :raise OSError: if cannot open the file.
        """
        checksum = md5()

        with src.open('rb') as f:  # Can raise OSError
            for chunk in iter(lambda: f.read(4096), b''):
                checksum.update(chunk)

        return checksum.hexdigest()

    def add(
            self,
            new: Iterable[Union[Path, Tuple[Path, str]]]) -> List[
                Union[Object, CloudStubObject]]:
        """Add files to the :attr:`container`.

        New names can be given to the files, by using tuples, e.g.::

            cloud_files.add([(some_file, 'new_name.txt')])

        Otherwise, the original file paths are used.

        :raise OSError:
            if cannot open a file locally to read its content.
        :raise ~.CloudUploadError:
            if something wrong happens during files upload.
        """
        added = []

        for static_file in new:
            try:
                src, dst = static_file
            except TypeError:
                obj = self.upload(static_file)
            else:
                obj = self.upload(src, dst)

            added.append(obj)

        return added

    def replace(
            self,
            existing: Iterable[Union[Path, Tuple[Path, str]]]) -> List[
                Union[Object, CloudStubObject]]:
        """Replace files inside the :attr:`container`.

        If remote names differ from local names, tuples can be used, e.g.::

            cloud_files.replace([(some_file, 'remote_name.txt')])

        Otherwise, the original file paths are used.

        :raise OSError:
            if cannot open a file locally to read its content.
        :raise ~.CloudFileNotFound:
            when trying to replace a file which doesn't exist remotely.
        :raise ~.CloudError:
            when cannot fetch information about the remote file to replace.
        :raise ~.CloudUploadError:
            if something wrong happens during files upload.
        """
        replaced = []

        for static_file in existing:
            try:
                src, dst = static_file
            except TypeError:
                src = static_file
                dst = str(static_file)
                local_hash = self.md5sum(static_file)
            else:
                local_hash = self.md5sum(src)

            try:
                obj = self.object_store.get_object(dst, self.container.name)
                remote_hash = obj.etag
            except ResourceNotFound:
                raise exceptions.CloudFileNotFound(self.container.name, dst)
            except SDKException as exc:
                raise exceptions.CloudError(exc)

            if local_hash != remote_hash:
                # Can raise OSError or CloudUploadError.
                obj = self.upload(src, dst)

            replaced.append(obj)

        return replaced

    def delete(self, existing: Iterable[Union[Path, str]]) -> None:
        """Remove files from the :attr:`container`.

        :raise ~.CloudFileNotFound:
            when trying to delete a file which doesn't exist.
        :raise ~.CloudError:
            if something wrong happens during deletion.
        """
        for static_file in existing:
            dst = str(static_file)

            try:
                self.object_store.delete_object(dst, container=self.container)
            except ResourceNotFound:
                raise exceptions.CloudFileNotFound(self.container.name, dst)
            except SDKException as exc:
                raise exceptions.CloudError(exc)

import asyncio
import logging
from hashlib import md5
from pathlib import Path
from typing import (
    BinaryIO, Callable, ContextManager, Dict, Iterable, List, Tuple, Union)

import openstack
from openstack.connection import Connection
from openstack.exceptions import ResourceNotFound, SDKException
from openstack.object_store.v1._proxy import Proxy as ObjectStore
from openstack.object_store.v1.container import Container
from openstack.object_store.v1.obj import Object

from website import exceptions
from website.stubs import (
    CloudStubContainer, CloudStubObject, CloudStubObjectStore)

logger = logging.getLogger(__name__)

CloudConnection = Union[Connection, 'CloudStubConnection']
CloudObject = Union[Object, CloudStubObject]
CloudContainer = Union[CloudStubContainer, Container]
CloudObjectStore = Union[CloudStubObjectStore, ObjectStore]
SourceFile = Path
RemoteName = str
FileUploads = Iterable[Union[SourceFile, Tuple[SourceFile, RemoteName]]]
UpdateConfirmation = ContextManager[Dict[str, Tuple[str]]]
UpdateResult = List[Union[Object, CloudStubObject]]


def connect(factory: Callable = openstack.connect):
    try:
        return factory()
    except SDKException as exc:
        raise exceptions.CloudConnectionFailure(exc)


class PrintMixin:
    def print(self, message):
        if not self.quiet:
            print(message, file=self.output)


# XXX: Rename in CloudUpdateManager? (03/2019)
class CloudFilesManager(PrintMixin):
    """...

    https://docs.openstack.org/openstacksdk/latest/user/proxies/object_store.html
    """  # noqa: E501
    def __init__(
            self, connection: CloudConnection, container: str,
            quiet: bool = False):
        try:
            self.object_store = connection.object_store
            self.container = self.object_store.get_container_metadata(container)  # noqa: E501
        except ResourceNotFound:
            raise exceptions.CloudContainerNotFound(container)
        except SDKException as exc:
            raise exceptions.CloudError(exc)

    # Main API

    def update(self, static_files: Path, confirm: bool = False):
        # Helpers to get the remote name of local files, and vice-versa.
        remote_name = (lambda src: str(src.relative_to(self.static_files)))
        local_path = (lambda dst: self.static_files / dst.name)

        # Retrieve the list of files to upload, and the ones already online.
        local_files = set(
            (src, remote_name(src))
            for src in self.static_files.rglob('*') if src.is_file()
        )

        try:
            remote_files = set(
                (local_path(dst), dst.name)
                for dst in self.object_store.objects(self.container)
            )
        except SDKException as exc:
            raise exceptions.CloudError(exc)

        # Compute the list of files to add, replace or delete.
        to_add = local_files - remote_files
        to_replace = local_files - to_add
        to_delete = remote_files - local_files

        if not to_add | to_replace | to_delete:
            self.print("Everything is up-to-date :)")
            return

        if confirm:
            result = {'new': to_add, 'outdated': to_replace, 'erased': to_delete}  # noqa: E501
            self.report(result)
            self.prompt.confirm()

        # Effectively update the remote files.
        added = self.add(to_add)
        replaced = self.replace(to_replace)
        self.delete([dst for _src, dst in to_delete])

        return added + replaced

    def report(self, result):
        def static_files_list(static_files):
            for _src, dst in static_files:
                self.print(f"- {dst}")

        if result['new']:
            self.print("New files to upload:")
            static_files_list(result['new'])

        if result['outdated']:
            self.print("Outdated files to replace:")
            static_files_list(result['outdated'])

        if result['erased']:
            self.print("Extra files to delete:")
            static_files_list(result['erased'])

    def add(self, new: FileUploads) -> List[CloudObject]:
        """Add files to the :attr:`container`.

        New names can be given to the files, by using tuples, e.g.::

            cloud_files.add([(some_file, 'new_name.txt')])

        Otherwise, the original file paths are used.

        :raise OSError:
            if cannot open a file locally to read its content.
        :raise ~.CloudUploadError:
            if something wrong happens during files upload.
        """
        if not new:
            return []

        async def upload(src, dst=None):
            obj = self.upload(src, dst)
            self.print("- {dst}")
            return obj

        async def main(new):
            to_add = []

            for static_file in sorted(new):
                try:
                    src, dst = static_file
                except TypeError:
                    to_add.append[upload(static_file)]
                else:
                    to_add.append[upload(src, dst)]

            self.print("Uploading new files:")
            await asyncio.gather(*to_add)

        return asyncio.run(main(new)).result()

    def replace(self, existing: FileUploads) -> List[CloudObject]:
        """Replace files inside the :attr:`container`.

        If remote names differ from local names, tuples can be used, e.g.::

            cloud_files.replace([(some_file, 'remote_name.txt')])

        Otherwise, the original file paths are used.

        Also, remote files are only replaced if they differ from their local
        source.

        :raise OSError:
            if cannot open a file locally to read its content.
        :raise ~.CloudFileNotFound:
            when trying to replace a file which doesn't exist remotely.
        :raise ~.CloudError:
            when cannot fetch information about the remote file to replace.
        :raise ~.CloudUploadError:
            if something wrong happens during files upload.
        """
        if not existing:
            return []

        async def compare(src, dst):
            return self.compare(src, dst)

        async def upload(src, dst):
            obj = self.upload(src, dst)
            self.print(f"- {dst}")
            return obj

        async def main():
            to_compare = []

            for static_file in existing:
                try:
                    src, dst = static_file
                except TypeError:
                    src = static_file
                    dst = str(static_file)

                to_compare.append[compare(src, dst)]

            result = await asyncio.gather(*to_compare)

            to_replace = [
                upload(to_compare[index])
                for index, comparison in enumerate(result)
                if comparison is True
            ]

            if not to_replace:
                return []

            self.print("Replacing outdated files:")
            await asyncio.gather(*to_replace)

        return asyncio.run(main()).result()

    def delete(self, existing: Iterable[Union[Path, str]]) -> None:
        """Remove files from the :attr:`container`.

        :raise ~.CloudFileNotFound:
            when trying to delete a file which doesn't exist.
        :raise ~.CloudError:
            if something wrong happens during deletion.
        """
        if not existing:
            return

        async def erase(dst):
            obj = self.erase(dst)
            self.print(f"- {dst}")
            return obj

        async def main(existing):
            tasks = [
                erase(str(static_file))
                for static_file in sorted(existing)
            ]
            self.print("Deleting extra files:")
            await asyncio.gather(*tasks)

        return asyncio.run(main(existing)).result()

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

    def upload(self, src: Path, dst: str = None) -> CloudObject:
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

    def compare(self, src: Path, dst: str) -> bool:
        local_hash = self.md5sum(src)

        try:
            obj = self.object_store.get_object(dst, self.container.name)
            remote_hash = obj.etag
        except ResourceNotFound:
            raise exceptions.CloudFileNotFound(self.container.name, dst)
        except SDKException as exc:
            raise exceptions.CloudError(exc)

        if local_hash != remote_hash:
            return False

        return True

    def erase(self, dst: str):
        try:
            self.object_store.delete_object(dst, container=self.container)
        except ResourceNotFound:
            raise exceptions.CloudFileNotFound(self.container.name, dst)
        except SDKException as exc:
            raise exceptions.CloudError(exc)

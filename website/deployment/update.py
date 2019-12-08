import asyncio
import logging
import sys
from hashlib import md5
from pathlib import Path
from typing import BinaryIO, Iterable, List, TextIO, Union

import aiofiles
from openstack.exceptions import ResourceNotFound, SDKException

from website.deployment import exceptions
from website.deployment.typing import (
    CloudConnection, CloudObject, FileUploads)

logger = logging.getLogger(__name__)


class CloudFilesManager:
    """...

    https://docs.openstack.org/openstacksdk/latest/user/proxies/object_store.html
    """  # noqa: E501
    def __init__(
            self, connection: CloudConnection, container: str,
            quiet: bool = False, output: TextIO = sys.stdout):
        self.quiet = quiet
        self.output = output

        try:
            self.object_store = connection.object_store
            self.container = self.object_store.get_container_metadata(container)
        except ResourceNotFound:
            raise exceptions.CloudContainerNotFound(container)
        except SDKException as exc:
            raise exceptions.CloudError(exc)

    # TODO: Test printing... (12/2019)
    def print(self, message: str):
        if not self.quiet:
            print(message, file=self.output)

    # Main API

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
            obj = await self.upload(src, dst)
            self.print(f"- {dst}")
            return obj

        async def main(new):
            to_add = []

            for static_file in sorted(new):
                try:
                    src, dst = static_file
                except TypeError:
                    to_add.append(upload(static_file))
                else:
                    to_add.append(upload(src, dst))

            self.print("Uploading new files:")
            return await asyncio.gather(*to_add)

        return asyncio.run(main(new))

    def replace(self, existing: FileUploads) -> List[CloudObject]:
        """Replace existing files inside the :attr:`container`.

        If remote names differ from local names, tuples can be used, e.g.::

            cloud_files.replace([(some_file, 'remote_name.txt')])

        Otherwise, the original file paths are used.

        Also, remote files are only replaced if they differ from their local source.

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

        async def replace(src, dst):
            src_changed = not await self.compare(src, dst)

            if src_changed:
                obj = await self.upload(src, dst)
                self.print(f"- {dst}")
                return obj

        async def main(existing):
            to_replace = []

            for static_file in existing:
                try:
                    src, dst = static_file
                except TypeError:
                    src = static_file
                    dst = str(static_file)

                to_replace.append(replace(src, dst))

            self.print("Replacing outdated files:")
            replaced = [obj for obj in await asyncio.gather(*to_replace) if obj]

            return replaced

        return asyncio.run(main(existing))

    def delete(self, existing: Iterable[Union[Path, str]]) -> None:
        """Remove files from the :attr:`container`.

        :raise ~.CloudFileNotFound:
            when trying to delete a file which doesn't exist.
        :raise ~.CloudError:
            if something wrong happens during deletion.
        """
        if not existing:
            return

        async def delete(dst):
            obj = await self.erase(dst)
            self.print(f"- {dst}")
            return obj

        async def main(existing):
            to_delete = [
                delete(str(static_file))
                for static_file in sorted(existing)
            ]
            self.print("Deleting extra files:")
            return await asyncio.gather(*to_delete)

        return asyncio.run(main(existing))

    # Helpers

    @staticmethod
    async def md5sum(src: Path) -> str:
        """Compute MD5 hash of a file located at ``src``.

        :raise OSError: if cannot open the file.
        """
        checksum = md5()

        async with aiofiles.open(str(src), 'rb') as f:  # Can raise OSError
            while True:
                chunk = await f.read(4096)

                if chunk == b'':
                    break

                checksum.update(chunk)

        return checksum.hexdigest()

    async def upload(self, src: Path, dst: str = None) -> CloudObject:
        """Upload the content of a file located at ``src``.

        The file's path is used to name the file in the :attr:`container`.

        :param dst: optional new name/path to give to the file once uploaded.
        :raise OSError: if cannot open a file locally to read its content.
        :raise ~.CloudUploadError: if something wrong happens during upload.
        """
        dst = dst or str(src)

        async with aiofiles.open(str(src), 'rb') as source:  # Can raise OSError
            data = await source.read()

        try:
            return self.object_store.upload_object(self.container, dst, data=data)
        except SDKException as exc:
            raise exceptions.CloudUploadError(exc)

    async def download(self, dst: str) -> BinaryIO:
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

    async def compare(self, src: Path, dst: str) -> bool:
        local_hash = await self.md5sum(src)

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

    async def erase(self, dst: str):
        try:
            self.object_store.delete_object(dst, container=self.container)
        except ResourceNotFound:
            raise exceptions.CloudFileNotFound(self.container.name, dst)
        except SDKException as exc:
            raise exceptions.CloudError(exc)

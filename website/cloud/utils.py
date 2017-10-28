"""Util functions to be used for making scripts.

They all contain side effects and are not tested!
"""
from hashlib import md5
import logging

from rackspace.connection import Connection
from openstack.exceptions import SDKException

logger = logging.getLogger(__name__)


# Cloud Connection

def connect_to_the_cloud(username, api_key, region, cls=Connection):
    try:
        connection = cls(username=username, api_key=api_key, region=region)
        return connection
    except SDKException as exc:
        logger.error("Cannot connect to the Cloud: %s", exc)
        raise


def retrieve_container(object_store, container_name):
    container = filter(
        lambda c: c['name'] == container_name,
        object_store.containers())

    try:
        return next(container)
    except SDKException as exc:
        error = 'Unable to retrieve container "%s": %s'
        logger.error(error, container_name, exc)
        raise


def retrieve_objects(object_store, container):
    try:
        return {obj.name: obj for obj in object_store.objects(container)}
    except SDKException as exc:
        logger.error("Unable to retrieve list of remote files: %s", exc)
        raise


# Objects Management

def delete_outdated_files(object_store, container, files):
    if files:
        logger.info("Deleting outdated remote files...")

        for file_path in sorted(files):
            try:
                object_store.delete_object(file_path, container=container)
            except SDKException as exc:
                logger.error("Couldn't delete %s: %s", file_path, exc)
            else:
                logger.info("%s deleted", file_path)
    else:
        logger.info("No remote file to delete")


def upload_file(object_store, container, file_path, data):
    try:
        object_store.upload_object(
            container=container, name=file_path, data=data)
    except SDKException as exc:
        logger.error("Couldn't upload %s: %s", file_path, exc)
    else:
        logger.info("%s uploaded", remote_path)


def upload_existing_files(object_store, container, files):
    logger.info("Comparing existing files...")
    files_updated = False

    for remote_path, local_path in sorted(files.items()):
        # TODO: add test for Cloud objects, when not providing binary data
        content = local_path.open('rb').read()
        local_hash = md5(content).hexdigest()
        remote_hash = \
            object_store.get_object_metadata(remote_path, container).etag

        if local_hash != remote_hash:
            upload_file(object_store, container, remote_path, data)
            files_updated = True

    if not files_updated:
        logger.info("No remote file to update")


def upload_new_files(object_store, container, files):
    if files:
        logger.info("Uploading new files...")

        for remote_path, local_path in sorted(files.items()):
            try:
                data = local_path.open('rb').read()
            except OSError as exc:
                logger.error("Couldn't read content of %s: %s", local_path, exc)
                continue

            upload_file(object_store, container, remote_path, data)
    else:
        logger.info("No new file to upload")

"""Types specific to Cloud deployment."""

from pathlib import Path
from typing import ContextManager, Dict, Iterable, List, Tuple, Union

from openstack.connection import Connection
from openstack.object_store.v1._proxy import Proxy as ObjectStore
from openstack.object_store.v1.container import Container
from openstack.object_store.v1.obj import Object

from website.deployment.stubs import (
    CloudStubConnection, CloudStubContainer, CloudStubObject, CloudStubObjectStore)

CloudConnection = Union[Connection, CloudStubConnection]
CloudObject = Union[Object, CloudStubObject]
CloudContainer = Union[CloudStubContainer, Container]
CloudContainers = List[Union[Container, CloudStubContainer]]
CloudObjectStore = Union[CloudStubObjectStore, ObjectStore]
SourceFile = Path
RemoteName = str
FileUploads = Iterable[Union[SourceFile, Tuple[SourceFile, RemoteName]]]
UpdateConfirmation = ContextManager[Dict[str, Tuple[str]]]
UpdateResult = List[Union[Object, CloudStubObject]]

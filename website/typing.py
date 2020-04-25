"""Global type hints."""

from typing import Union

from website.base.models import BaseDocument
from website.models import Category, Tag

# TODO: Rename to BaseDocumentModel (04/2020)
Document = BaseDocument
Metadata = Union[Category, Tag]

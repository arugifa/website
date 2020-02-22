"""Global type hints."""

from pathlib import Path, PurePath
from typing import Any, Dict, List, Mapping, Set, Union

from website.base.handlers import BaseDocumentFileHandler
from website.base.models import BaseModel
from website.exceptions import DocumentParsingError, DocumentProcessingError


# Content

SourceFilePath = Union[Path, PurePath]  # For PROD and TESTS


# Content Management

Content = Union[BaseModel, List[BaseModel]]
ContentDeletionResult = List[SourceFilePath]
ContentHandlers = Mapping[str, BaseDocumentFileHandler]
ContentOperationResult = Dict[str, BaseModel]
ContentOperationErrors = Dict[str, Exception]
ContentUpdateErrors = Dict[str, Union[Dict[str, Exception], List[Exception]]]
ContentUpdatePlan = Dict[str, List[Path]]
ContentUpdatePlanErrors = List[Exception]
ContentUpdateResult = Dict[str, Dict[str, Content]]


# Source File Processing

ProcessingResult = Dict[str, Any]
ProcessingErrorSet = Set[Union[DocumentProcessingError, DocumentParsingError]]


# Source Parsing

ParsingErrorSet = Set[DocumentParsingError]

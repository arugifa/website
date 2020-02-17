"""Global type hints."""

from typing import Any, Dict, Set, Union

from website.exceptions import DocumentParsingError, DocumentProcessingError


# Source File Processing
ProcessingResult = Dict[str, Any]
ProcessingErrorSet = Set[Union[DocumentProcessingError, DocumentParsingError]]

# Source Parsing
ParsingErrorSet = Set[DocumentParsingError]

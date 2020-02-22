"""Base type hints."""

from typing import Any, Iterable

import tqdm


# Updates

UpdateErrors = Iterable
UpdatePlan = Any
UpdateProgress = tqdm.tqdm
UpdateResult = Any

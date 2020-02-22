"""Base classes to manage updates."""

import re
import sys
from abc import ABC, abstractmethod
from collections import deque
from contextlib import AbstractAsyncContextManager, contextmanager
from typing import Any, Callable, ClassVar, Dict, Iterable, TextIO, Union

from tqdm import tqdm

from website import exceptions


class BaseUpdateRunner:

    def __init__(
            self, manager: Any, *,
            prompt: 'Prompt' = None, output: TextIO = sys.stdout):

        self.manager = manager
        self.prompt = prompt or Prompt(output=output)
        self.output = output

    # Abstract Attributes

    @abstractproperty
    def preview(self) -> str:
        pass

    @abstractproperty
    def report(self) -> str:
        pass

    @abstractmethod
    async def _plan(self) -> Tuple[UpdatePlan, UpdateErrors]:
        pass

    @abstractmethod
    async def _run(self) -> Tuple[UpdateResult, UpdateErrors]:
        """:return: update result and potential errors."""

    # Properties

    @property
    def errors(self) -> UpdateErrors:
        if not self._errors:
            raise UpdateNotRun

        return self._errors

    @property
    def progress(self) -> UpdateProgress:
        return self._progress

    @property
    def result(self) -> UpdateResult:
        if not self._result:
            raise UpdateNotRun

        return self._result

    @property
    def todo(self) -> UpdatePlan:
        if not self._todo:
            raise UpdatePlanNotRun

        return self._todo

    # Main API

    async def plan(self) -> UpdatePlan:
        self._todo, self._errors = await self._plan()

        if self._errors:
            raise UpdatePlanError(self.preview)

        print(self.preview, file=self.output)
        return self._todo

    def confirm(self) -> None:
        try:
            self.prompt.confirm()
        except AssertionError:
            raise UpdateAborted()

    async def run(self) -> UpdateResult:
        self._result, self._errors = await self._run()

        if self._errors:
            raise UpdateFailed(self.report)

        print(self.report, file=self.output)
        return self._result

    # Helpers

    @contextmanager
    def progress_bar(self, *, total: int) -> None:
        try:
            with tqdm(total=total, file=self.output) as pbar:
                self._progress = pbar
                yield
        finally:
            self._progress = None


class Prompt(ABC):
    """Helper to interactively ask questions to an user during an update.

    Useful when an update cannot be performed totally automatically.

    :param input:
        function to use for recording user's answers.
        Must have an API similar to :func:`input`.
    :param output:
        text stream to use for writing (and most probably printing) questions.
    """

    def __init__(self, *, input: Callable = input, output: TextIO = sys.stdout):
        self.input = input
        self.output = output

    def ask(self, question: str, default_answer: str = None) -> str:
        """Ask a question to the user.

        :param question:
            the question to ask.
        :param default_answer:
            default answer to use when the user doesn't provide one.
            When no default answer is defined, then the question is asked again until
            the user effectively provides an answer.
        :return:
            the user's answer (or the default one, if defined).
        """
        while not (answer := self.input(question) or default_answer):
            continue
        else:
            return answer

    def confirm(self) -> None:
        """Ask for confirmation to the user before performing an action.

        Useful for example to ask for pursuing the update, after having displayed a
        report about changes to be made.

        :raise AssertionError: if the user prefers to cancel.
        """
        yes = r'^\s*y(es)?\s*$'
        answer = self.ask("Do you want to continue? [Y/n] ", default='y')
        assert re.match(yes, answer, flags=re.I)

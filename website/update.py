import re
import sys
from abc import ABC, abstractmethod
from collections import deque
from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, ClassVar, Dict, TextIO

from website import exceptions


class BaseUpdateManager(ABC):
    runner: ClassVar['BaseUpdateRunner']

    def __init__(self, *args, prompt: 'ShellPrompt', **kwargs):
        self.prompt = prompt

    @abstractmethod
    def update(self, *args, **kwargs) -> 'BaseUpdateRunner':
        """Prepare update."""
        pass


class BaseUpdateRunner(AbstractAsyncContextManager):

    def __init__(self, *args, manager: BaseUpdateManager):
        self.manager = manager
        self._todo = None
        self._preview = None

    async def __aenter__(self) -> 'BaseUpdateRunner':
        self.todo = await self.plan()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.cancel()

    @property
    def todo(self) -> Dict[str, Any]:
        if not self._todo:
            self._todo = self.plan()

        return self._todo

    @todo.setter
    def todo(self, value: Dict[str, Any]) -> None:
        self._todo = value

    @property
    def preview(self) -> str:
        """Generate a default preview."""
        if not self._preview:
            self._preview = self.generate_preview()

        return self._preview

    # Main API

    async def run(self) -> Any:
        self.todo = self.plan()
        await self.proceed()

    @abstractmethod
    async def plan(self) -> Dict[str, Any]:
        # XXX: Make it async if needed in the future (03/2019)
        pass

    def confirm(self) -> None:
        """...

        :raise UpdateAborted: ...
        """
        try:
            self.manager.prompt.confirm(self.preview)
        except AssertionError:
            raise exceptions.UpdateAborted(self)

    async def cancel(self) -> None:
        """...

        Can do whatever here, like logging something...
        """
        pass

    @abstractmethod
    async def proceed(self) -> None:
        pass

    # Helpers

    @abstractmethod
    def generate_preview(self, **kwargs) -> str:
        """Generate an update preview.

        The preview can be customized by subclasses with additional keyword
        arguments. Useful for example to generate text or HTML previews.
        """
        pass


class ShellPrompt(ABC):
    def __init__(self, *, input: Callable = input, output: TextIO = sys.stdout):  # noqa: E501
        self.input = input
        self.output = output

    @property
    @abstractmethod
    def questions(self):
        pass

    def ask_for(self, topic, **details):
        question = self.questions[topic].format(**details)
        return self.ask(question)

    def ask(self, question, default_answer=None):
        answer = None

        def ask_again(question):
            return self.input(question) or default_answer

        # TODO: Use an assignment expression instead with Python 3.8 (03/2019)
        # See https://www.python.org/dev/peps/pep-0572/
        while not answer:
            answer = ask_again(question)

        return answer

    def confirm(self, todo: str):
        """...

        :raise AssertionError: ...
        """
        print(todo, file=self.output)

        yes = r'^\s*y(es)?\s*$'
        answer = self.ask("Do you want to continue? [Y/n] ", default='y')
        assert re.match(yes, answer, flags=re.I)


class AsyncShellPrompt(ShellPrompt):
    def __init__(self, *args, **kwargs):
        ShellPrompt.__init__(self, *args, **kwargs)
        self.quiz = deque()

    def solve_later(self, problem):
        self.quiz.append(problem)

    def ask_for_later(self, topic, callback: Callable, **details) -> None:
        question = self.questions[topic].format(**details)
        self.quiz[question].append(callback)

    def answer_quiz(self):
        while self.quiz:
            problem = self.quiz.popleft()
            problem()

    def answer_quiz_bck(self):
        while self.quiz:
            problem, callbacks = self.quiz.popitem()

            solution = None
            answer = self.ask(problem)

            for callback in callbacks:
                solution = callback(answer, solution)

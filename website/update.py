"""Collection of classes to manage website updates."""
# TODO: Write tests before merging DEV into MASTER (05/2019)

import re
import sys
from abc import ABC, abstractmethod
from collections import deque
from typing import Callable, Dict, TextIO, Union


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

    @property
    @abstractmethod
    def questions(self) -> Dict[Union[str, object], str]:
        """Predefined questions to ask during an update.

        To be used in conjunction with :meth:`~.ask_for`.

        Questions should be classified by topic, e.g.::

            {
                'first_name': "What's your first name?",
                'last_name': "What's your last name?",
            }

        Templates can also be used (see :meth:`~.ask_for` for more info)::

            {
                'first_name': "What's the first name of {user}?",
                'last_name': "What's the last name of {user}?",
            }

        Finally, objects can also be used to classify questions::

            {
                UserName: "What's the user's name?",
                ProjectName: "What's the project's name?",
            }
        """

    def ask_for(self, topic: Union[str, object], **details: str) -> str:
        """Ask for a predefined question about a specific topic.

        Questions are stored in :meth:`~.questions`, and can be personalized by giving
        additional keyword arguments.

        :return: the user's answer.
        """
        question = self.questions[topic].format(**details)
        return self.ask(question)

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
        answer = None

        def ask_again(question):
            return self.input(question) or default_answer

        # TODO: Use an assignment expression instead with Python 3.8 (03/2019)
        # See https://www.python.org/dev/peps/pep-0572/
        while not answer:
            answer = ask_again(question)

        return answer

    def confirm(self, todo: str) -> None:
        """Ask for confirmation to the user before performing an action.

        Useful for example to ask for pursuing the update, after having displayed a
        report about changes to be made.

        :raise AssertionError: if the user prefers to cancel.
        """
        print(todo, file=self.output)

        yes = r'^\s*y(es)?\s*$'
        answer = self.ask("Do you want to continue? [Y/n] ", default='y')
        assert re.match(yes, answer, flags=re.I)


class AsyncPrompt(Prompt):
    """Helper to asynchronously ask questions to an user during an update.

    Useful when performing the update's steps in parralel, and that some questions
    should be asked when all steps have been completed, in order to not block their
    execution.
    """

    def __init__(self, *args, **kwargs):
        Prompt.__init__(self, *args, **kwargs)
        self.quiz = deque()

    def solve_later(self, problem: Callable) -> None:
        """Store in :attr:`~.quiz` a problem to be solved later on.

        A problem is just a function which will be executed to ask one or more
        questions, and to perform actions using answers provided by the user::

            prompt = AsyncPrompt()

            def username_update(db):
                current = prompt.ask_question("What's the user you want to update?")
                user = db.find_user(name=current)

                new = prompt.ask_question("What's the new user's name?")
                user.name = new
                user.save()

            prompt.solve_later(username_update)

        Problems can be solved one after another by calling :meth:`~.answer_quiz`.
        """
        self.quiz.append(problem)

    def answer_quiz(self) -> None:
        """Ask the user to solve all problems stored in :attr:`~.quiz`."""
        while self.quiz:
            problem = self.quiz.popleft()
            problem()

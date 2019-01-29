import sys
from collections import defaultdict
from functools import partial
from pathlib import Path
from subprocess import PIPE, run
from typing import Callable, Dict, Mapping, TextIO, Union


class Repository:
    """...

    :param path: repository's path, relative or absolute.
    """

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path).resolve()

    def diff(
            self, from_commit: str, to_commit: str = 'HEAD',
            shell: Callable = None, output: TextIO = None) -> Dict[str, Path]:  # noqa: E501
        """Return diff between two commits.

        :param run:
            callback for running ``git diff``; defaults to :func:`subprocess.run`.
            Must return an object with a ``stdout`` attribute,
            similar to :fun:`subprocess.run'.
        :param from_commit:
            commit to compare to.
        :param to_commit:
            reference commit.
        :return:
            list of paths relative to the repository.
        """
        shell = shell or partial(run, check=True, cwd=self.path, stdout=PIPE, encoding='utf-8')

        cmdline = f'git diff --name-status {from_commit} {to_commit}'
        # Discard last new line character.
        output = shell(cmdline).stdout.split('\n')[:-1]

        diff = defaultdict(list)

        for line in output:
            status, *files = line.split('\t')
            paths = [Path(f) for f in files]

            # We only check the first letter of the status,
            # because when a file is renamed, the status is
            # followed by a score of similarity.
            if status.startswith('R'):
                diff['R'].append(tuple(paths))
            else:
                diff[status[0]].append(paths[0])

        if output:
            self.print_diff(diff, output)

        return {
            'added': diff['A'],
            'modified': diff['M'],
            'renamed': diff['R'],
            'deleted': diff['D'],
        }

    @staticmethod
    def print_diff(diff: Mapping, output: TextIO = sys.stdout):
        """Print Git diff."""
        for action, files in diff.items():
            if files:
                print(f'The following files have been {action}:', file=output)

                for f in files:
                    if isinstance(f, tuple):
                        # - src_file -> dst_file
                        print('- ', end='', file=output)
                        print(*f, sep=' -> ', file=output)
                    else:
                        print(f'- {f}', file=output)

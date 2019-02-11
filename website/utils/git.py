import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, Mapping, TextIO, Union

from website.utils import BaseCommandLine


class Repository(BaseCommandLine):
    """...

    :param path: repository's path, relative or absolute.
    """

    def __init__(self, path: Union[str, Path], shell: Callable = None):
        BaseCommandLine.__init__(self, shell)
        self.path = Path(path).resolve()

    def diff(
            self, from_commit: str, to_commit: str = 'HEAD',
            display=False, output: TextIO = sys.stdout) -> Dict[str, Path]:  # noqa: E501
        """Return diff between two commits.

        :param from_commit:
            commit to compare to.
        :param to_commit:
            reference commit.
        :return:
            list of paths relative to the repository.
        """
        cmdline = f'git diff --name-status {from_commit} {to_commit}'

        with self.cwd(self.path):
            # Discard last new line character.
            output = self.run(cmdline).split('\n')[:-1]

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

        if display:
            self.print_diff(diff, output)

        return {
            'added': diff['A'],
            'modified': diff['M'],
            'renamed': diff['R'],
            'deleted': diff['D'],
        }

    @staticmethod
    def print_diff(diff: Mapping, output: TextIO = sys.stdout) -> None:
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

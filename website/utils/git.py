import sys
from collections import defaultdict
from pathlib import PurePath


def get_diff(run, from_commit, to_commit='HEAD'):
    """Return diff between two commits.

    :param function run: callback for running ``git diff``.
    :param str from_commit: commit to compare to.
    :param str to_commit: reference commit.
    """
    diff = defaultdict(list)

    cmdline = f'git diff --name-status {from_commit} {to_commit}'
    # Discard last new line character.
    output = run(cmdline).stdout.split('\n')[:-1]

    for line in output:
        status, *files = line.split('\t')
        files = [PurePath(f) for f in files]

        # We only check the first letter of the status,
        # because when a file is renamed, the status is
        # followed by a score of similarity.
        if status[0] == 'R':
            diff['R'].append(files)
        else:
            diff[status[0]].append(files[0])

    return (
        diff['A'],  # New files
        diff['M'],  # Modified files
        diff['R'],  # Renamed files
        diff['D'],  # Deleted files
    )


def print_diff(new, modified, renamed, deleted, stream=sys.stdout):
    def print_files(action, files):
        if files:
            print(f'The following files will be {action}:', file=stream)

            for f in files:
                if isinstance(f, list):
                    # - src_file -> dst_file
                    print('- ', end='', file=stream)
                    print(*f, sep=' -> ', file=stream)
                else:
                    print(f'- {f}', file=stream)

    print_files('imported', new)
    print_files('updated', modified)
    print_files('renamed', renamed)
    print_files('removed', deleted)

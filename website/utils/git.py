from collections import defaultdict


def get_diff(run, from_commit, to_commit='HEAD'):
    """Return diff between two commits.

    :param function run:
        callback for running ``git diff``.
        Must return an object with a ``stdout`` attribute,
        similar to :fun:`subprocess.run'.
    :param str from_commit:
        commit to compare to.
    :param str to_commit:
        reference commit.
    """
    diff = defaultdict(list)

    cmdline = f'git diff --name-status {from_commit} {to_commit}'
    # Discard last new line character.
    output = run(cmdline).stdout.split('\n')[:-1]

    for line in output:
        status, *files = line.split('\t')

        # We only check the first letter of the status,
        # because when a file is renamed, the status is
        # followed by a score of similarity.
        if status[0] == 'R':
            diff['R'].append(tuple(files))
        else:
            diff[status[0]].append(files[0])

    return (
        diff['A'],  # New files
        diff['M'],  # Modified files
        diff['R'],  # Renamed files
        diff['D'],  # Deleted files
    )


def print_diff(stream, diff):
    added, modified, renamed, deleted = diff

    def print_files(action, files):
        if files:
            print(f'The following files have been {action}:', file=stream)

            for f in files:
                if isinstance(f, tuple):
                    # - src_file -> dst_file
                    print('- ', end='', file=stream)
                    print(*f, sep=' -> ', file=stream)
                else:
                    print(f'- {f}', file=stream)

    print_files('added', added)
    print_files('modified', modified)
    print_files('renamed', renamed)
    print_files('deleted', deleted)

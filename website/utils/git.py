import sys


def parse_diff(diff):
    changes = defaultdict(list)

    for line in diff:
        status, *files = line.split('\t')
        files = [PurePath(f) for f in files]

        # We only check the first letter of the status,
        # because when a file is renamed, the status is
        # followed by a score of similarity.
        if status[0] == 'R':
            changes['R'].append(files)
        else:
            changes[status[0]].append(files[0])

    return changes


def print_diff(diff, stream=sys.stdout):
    def print_files(files):
        if files:
            print(f'The following files will be {action}:', file=stream)

            for f in files:
                if isinstance(f, list):
                    # - src_file -> dst_file
                    print('- ', end='', file=stream)
                    print(*f, sep=' -> ', file=stream)
                else:
                    print(f'- {f}', file=stream)

    print_files('imported', diff['A'])
    print_files('updated', diff['M'])
    print_files('renamed', diff['R'])
    print_files('removed', diff['D'])

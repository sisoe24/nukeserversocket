from __future__ import annotations

import pathlib
import argparse
import subprocess


def bump_version(version: str) -> None:
    cwd = pathlib.Path(__file__).parent
    dist = cwd / 'dist'
    dist.mkdir(exist_ok=True)

    version = subprocess.run(
        ['poetry', 'version', '-s', version], cwd=cwd, capture_output=True
    ).stdout.decode().strip()

    with open(cwd / 'nukeserversocket' / 'version.py', 'w') as f:
        f.write(f"__version__ = '{version}'")

    subprocess.run(['git', 'archive', '-o', f'{dist}/nukeserversocket.zip', 'HEAD'], cwd=cwd)


def get_parser():

    parser = argparse.ArgumentParser(
        description='NukeServerSocket - Build Manager',
    )

    parser.add_argument(
        '-b',
        '--bump',
        type=str,
        metavar='VERSION',
        help='''
        Bump the version of the package. A valid version string must be provided.
        Valid versions are the same as the ones accepted by poetry version command.
        Bumping the version will also build the package and create a new release.
        '''
    )

    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    if args.bump:
        bump_version(args.bump)
    else:
        parser.print_help()

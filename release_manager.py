from __future__ import annotations

import pathlib
import argparse
import subprocess

CWD = pathlib.Path(__file__).parent
DIST = CWD / 'dist'
DIST.mkdir(exist_ok=True)


def build() -> None:
    subprocess.run(
        ['git', 'archive', '-o', f'{DIST}/nukeserversocket.zip', 'HEAD'],
        cwd=CWD
    )


def bump_version(version: str) -> None:
    version = subprocess.run(
        ['poetry', 'version', '-s', version], cwd=CWD, capture_output=True
    ).stdout.decode().strip()

    with open(CWD / 'nukeserversocket' / 'version.py', 'w') as f:
        f.write(f"__version__ = '{version}'")

    build()


def get_parser():

    parser = argparse.ArgumentParser(
        description='NukeServerSocket - Build Manager',
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--build', action='store_true', help='Build the package.')

    group.add_argument(
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
    elif args.build:
        build()
    else:
        parser.print_help()

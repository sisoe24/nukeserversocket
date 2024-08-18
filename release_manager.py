from __future__ import annotations

import sys
import argparse
import subprocess
from typing import List
from pathlib import Path
from datetime import datetime
from textwrap import dedent

ROOT = Path(__file__).parent.parent
DIST = ROOT / 'dist'
DIST.mkdir(exist_ok=True)

PACKAGE = ROOT.name

Subparser = argparse._SubParsersAction[argparse.ArgumentParser]


def bump_version(version: str) -> None:

    version = subprocess.run(
        ['poetry', 'version', '-s', version], cwd=ROOT, capture_output=True
    ).stdout.decode().strip()

    with open(ROOT / PACKAGE / 'version.py', 'w') as f:
        f.write(f"__version__ = '{version}'\n")

    print(f'Version bumped to {version}')


def make_release():
    def format_output(files: list[Path]):
        max_length = max(len(f.name) for f in files)
        output: List[str] = []
        for i, f in enumerate(files, 1):
            date = datetime.fromtimestamp(
                f.lstat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            output.append(f'[{i}]: {f.name.ljust(max_length)} - {date}')
        return '\n'.join(output)

    try:
        subprocess.run(['gh', '--version'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print('gh command not found. Please install gh CLI.', file=sys.stderr)
        sys.exit(1)

    version = subprocess.run(
        ['poetry', 'version', '-s'], cwd=ROOT, capture_output=True
    ).stdout.decode().strip()

    print(f"Select the asset to release for version {version}:")
    files = sorted([f for f in DIST.iterdir() if not f.name.startswith('.')])
    index = input('[0]: Skip asset\n' + format_output(files) + '\n> ')

    version = f'v{version}'
    cmd = ['gh', 'release', 'create', version, '--notes', f'Release: {version}']
    if index != '0':
        cmd.append(str(files[int(index)-1]))

    subprocess.run(cmd, cwd=ROOT)


def build_parser(subparser: Subparser) -> None:

    def build(args: argparse.Namespace):

        if args.version:
            bump_version(args.version)

        if args.format == 'git':
            subprocess.run(
                ['git', 'archive', '-o', f'{DIST}/{args.name}.zip', 'HEAD'],
                cwd=ROOT
            )

        elif args.format == 'poetry':
            subprocess.run(['poetry', 'build'], cwd=ROOT)

        if args.release:
            make_release()

    parser = subparser.add_parser(
        'build', help='Build the package.',
        usage=dedent('''
        %(prog)s [options]

        Example:
            %(prog)s --name mypackage --version 0.1.0 --format git
            %(prog)s --format poetry
    '''),
    )
    parser.add_argument('--name', default=PACKAGE,
                        help='The name of the package.')
    parser.add_argument('--version', type=str, metavar='VERSION',
                        help='The version of the package.')
    parser.add_argument('--format', choices=['git', 'poetry'], default='git',
                        help='The format of the package. Default is git (zip).')
    parser.add_argument('--release', action='store_true',
                        help='Create a new release (requires `gh` command).')
    parser.set_defaults(func=build)


def main():

    parser = argparse.ArgumentParser(description=f'{PACKAGE} - Build Manager')

    subparsers = parser.add_subparsers(title='Commands')
    build_parser(subparsers)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--bump', type=str, metavar='VERSION',
                       help='Bump the version of the package.')

    args = parser.parse_args()
    if args.bump:
        bump_version(args.bump)
        sys.exit(0)

    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()

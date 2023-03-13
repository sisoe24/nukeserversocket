"""Generate about information for the user or bug reports."""
# coding: utf-8
from __future__ import print_function, with_statement

import os
import re
import platform
from collections import namedtuple

from PySide2 import __version__ as PySide2_Version
from PySide2.QtCore import QSysInfo
from PySide2.QtCore import __version__ as QtCore_version


def about():
    """Generate about information with various app versions.

    Returns:
        (tuple): a tuple containing tuple(str, str) with about information
    """
    _about = (
        ('NukeServerSocket', _get_package_version()),
        ('PySide2', PySide2_Version),
        ('PySide2.QtCore', QtCore_version),
        ('Machine', QSysInfo().prettyProductName()),
        ('Branch', _get_git_branch()),
        ('Python', platform.python_version()),
        ('Other', '')
    )

    return _convert_namedtuple(_about)


def about_links():
    """Generate About web link information.

    Returns:
        (tuple): a tuple containing tuple(str, str) with about information
    """
    github_web = 'https://github.com/sisoe24/NukeServerSocket'

    _about_links = (
        ('Github', github_web),
        ('Readme', github_web + '/blob/main/README.md'),
        ('Changelog', github_web + '/blob/main/CHANGELOG.md'),
        ('Issues', github_web + '/issues'),
        ('Nukepedia', 'https://www.nukepedia.com/python/misc/nukeserversocket'),
        ('Logs', 'file:///%s/nukeserversocket/logs' % _get_root()),
        ('Client apps', 'https://github.com/sisoe24/NukeServerSocket#11-client-applications'),
        ('Other', '')
    )

    return _convert_namedtuple(_about_links)


def _convert_namedtuple(_list):
    """Convert a list of tuples to a list of namedtuples.

    If tuple has an empty value, it will get removed.

    Returns:
        AboutData: a namedtuple with the key `label` and `repr`.
    """
    AboutData = namedtuple('AboutData', ['label', 'repr'])
    return [AboutData(k, v.strip()) for k, v in _list if v]


def _get_git_branch():
    """Get git branch name if any."""
    branch = ''

    head_file = os.path.join(_get_root(), '.git', 'HEAD')
    if os.path.exists(head_file):
        with open(head_file) as file:
            branch = file.read().split('/')[-1]

    return branch.strip()


def _get_root():
    """Get root (package) absolute path."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_package_version():
    """Get package version from pyproject.toml."""
    path = os.path.join(_get_root(), 'pyproject.toml')
    with open(path) as file:
        return re.search(r'(?<=version = ").+(?=")', file.read()).group()


def get_about_key(key):
    """Get a specific key in about. return empty string if not found."""
    return next((item[1] for item in about() + about_links() if key in item), '')


def about_to_string(exclude=None):
    """Get about dict and convert it into a multi line string.

    Args:
        exclude (list | str): A key to exclude in the return.
        could be a list of str keys or a simple string.
    """
    return ''.join(
        '%s: %s\n' % (key, value)
        for key, value in about()
        if not exclude or key not in exclude
    )

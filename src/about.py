# coding: utf-8
from __future__ import print_function

from os.path import (
    basename, join, exists
)

from subprocess import check_output
from collections import OrderedDict

from PySide2 import __version__ as PySide2_Version
from PySide2.QtCore import __version__ as QtCore_version
from PySide2.QtCore import QSysInfo

from . import nuke
from .utils import get_root


def get_git_branch():
    """Get git branch name if any."""
    branch = ""
    try:
        # git > 2.22 could do 'git branch --show-current'
        branch = check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'])

    # No git installed or project downloaded as a .zip
    except Exception:
        pass

    return branch.strip()


def _get_package_name():
    """Get package name."""
    return basename(get_root())


def _get_package_version():
    """Get package version. If no file return empty"""
    file = join(get_root(), 'VERSION')

    if exists(file):
        with open(file) as file:
            return file.read()

    return ''


package = _get_package_name()

about = OrderedDict([
    (package, _get_package_version()),
    ('PySide2', PySide2_Version),
    ('PySide2.QtCore', QtCore_version),
    ('Nuke', nuke.NUKE_VERSION_STRING),
    ('Machine', QSysInfo().prettyProductName()),
    ('Build', get_git_branch()),
    ('Github', 'https://github.com/sisoe24/' + package),
])


def about_to_string(exclude=None):
    """Get about dict and convert it into a multi line string.

    Args:
        exclude (list | str): list of str keys from the about dict to exclude in the return.
    """
    about_str = ''
    for key, value in about.items():
        if exclude:
            if key in exclude:
                continue
        about_str += '%s: %s\n' % (key, value)

    return about_str

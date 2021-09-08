# coding: utf-8
from __future__ import print_function, with_statement

import os
import platform
from os.path import (
    basename, join, exists, dirname, abspath
)


from PySide2 import __version__ as PySide2_Version
from PySide2.QtCore import __version__ as QtCore_version
from PySide2.QtCore import QSysInfo


def _get_git_branch():
    """Get git branch name if any."""
    branch = ""

    head_file = os.path.join(_get_root(), '.git', 'HEAD')
    if os.path.exists(head_file):
        with open(head_file) as file:
            branch = file.read().split('/')[-1]

    return branch.strip()


def _get_root():
    """Get root (package) absolute path."""
    return dirname(dirname(abspath(__file__)))


def _get_package_name():
    """Get package name."""
    return basename(_get_root())


def _get_package_version():
    """Get package version. If no file return empty"""
    file = join(_get_root(), 'VERSION')

    if exists(file):
        with open(file) as file:
            return file.read()

    return ''


PACKAGE = _get_package_name()


def _clean_empty(_list):
    """Don't include key if value is empty"""
    return [(k, v) for k, v in _list if v]


def about():
    _about = (
        (PACKAGE, _get_package_version()),
        ('PySide2', PySide2_Version),
        ('PySide2.QtCore', QtCore_version),
        ('Machine', QSysInfo().prettyProductName()),
        ('Branch', _get_git_branch()),
        ('Python', platform.python_version()),
        ('Other', '')
    )

    return _clean_empty(_about)


def about_links():
    github_web = 'https://github.com/sisoe24/' + PACKAGE

    _about_links = (
        ('Github', github_web),
        ('Readme', github_web + '/blob/main/README.md'),
        ('Changelog', github_web + '/blob/main/CHANGELOG.md'),
        ('Issues', github_web + '/issues'),
        ('Nukepedia', 'https://www.nukepedia.com/python/misc/nukeserversocket'),
        ('Logs', 'file:///%s/src/log' % _get_root()),
        ('Vscode Ext.', 'https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools'),
        ('Other', '')
    )

    return _clean_empty(_about_links)


def get_about_key(key):
    """Get a specific key in about. return empty string if not found."""
    abouts = about() + about_links()
    for item in abouts:
        if key in item:
            return item[1]
    return ''


def about_to_string(exclude=None):
    """Get about dict and convert it into a multi line string.

    Args:
        exclude (list | str): list of str keys from the about dict to exclude in the return.
    """
    about_str = ''
    for key, value in about():

        if exclude:
            if key in exclude:
                continue

        about_str += '%s: %s\n' % (key, value)

    return about_str

# coding: utf-8
from __future__ import print_function
"""Simple module for project details."""

import subprocess

from PySide2 import __version__ as pyside2_version
from PySide2.QtCore import __version__ as qtcore_version
from PySide2.QtCore import QSysInfo

from .env import get_env
from src import nuke


def get_git_branch():
    branch = ""
    try:
        # git > 2.22 could do 'git branch --show-current'
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'])

    # No git installed or project downloaded as a .zip
    except Exception:
        pass

    return branch


project_name = 'NukeServerSocket'
project_version = '0.0.1'
github = 'https://github.com/sisoe24/NukeServerSocket'


details = {
    project_name: project_version,
    'PySide2': pyside2_version,
    'PySide2.QtCore': qtcore_version,
    'Nuke': nuke.NUKE_VERSION_STRING,
    'Machine': QSysInfo().prettyProductName(),
    "Branch": get_git_branch()
}

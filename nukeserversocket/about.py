from __future__ import annotations

import os
import re
import pathlib
import sysconfig
from typing import Dict
from platform import python_version

from PySide2 import __version__ as PySide2_version

from .utils import cache


@cache
def load_version() -> str:
    # so much code to get the version number :(
    pyproject = pathlib.Path(__file__).parent.parent.parent / 'pyproject.toml'
    version = re.search(r'version = "(.*)"', pyproject.read_text())
    version = version[1] if version else 'unknown'
    os.environ['NUKE_SERVER_SOCKET_VERSION'] = version
    return version


def about() -> Dict[str, str]:
    """Return a dictionary with information about the application."""
    return {
        'version': load_version(),
        'python': python_version(),
        'pyside': PySide2_version,
        'machine': sysconfig.get_platform(),
        'user': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
    }

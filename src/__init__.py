import os
import subprocess

from PySide2 import __version__ as PySide2_Version
from PySide2.QtCore import __version__ as QtCore_version
from PySide2.QtCore import QSysInfo

from NukeServerSocket.src import logger

try:
    import nuke
except ImportError:
    from . import _nuke as nuke


def get_git_branch():
    """Get git branch name if any."""
    branch = ""
    try:
        # git > 2.22 could do 'git branch --show-current'
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'])

    # No git installed or project downloaded as a .zip
    except Exception:
        pass

    return branch


def get_package_name():
    package = os.path.basename(os.path.dirname(os.path.dirname(__file__)))
    return package


about = {
    get_package_name(): '0.0.1',
    'PySide2': PySide2_Version,
    'PySide2.QtCore': QtCore_version,
    'Nuke': nuke.NUKE_VERSION_STRING,
    'Machine': QSysInfo().prettyProductName(),
    'Build': get_git_branch(),
    'Github': 'https://github.com/sisoe24/' + get_package_name()
}

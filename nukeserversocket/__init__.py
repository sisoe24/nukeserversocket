"""Module will initialize the logging system and import Nuke."""
from __future__ import annotations

from .main import NukeServerSocket
from .controllers.nuke import install_nuke
from .version import __version__

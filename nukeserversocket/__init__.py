"""Module will initialize the logging system and import Nuke."""
from . import main, logger
from .refactor.main import NukeServerSocket
from .refactor.plugins.nuke import install_nuke

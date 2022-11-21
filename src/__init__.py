"""Module will initialize the logging system and import Nuke.

When testing plugin locally, a fake nuke module will be used instead. If
`import nuke` will fail it means that plugin is running locally, so import
`_nuke`. This will allow to call the nuke module outside Nuke without no module
found error.
"""
from . import logger
from . import main

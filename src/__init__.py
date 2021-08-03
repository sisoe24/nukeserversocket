from . import logger

try:
    import nuke
except ImportError:
    from . import _nuke as nuke
else:
    from . import main

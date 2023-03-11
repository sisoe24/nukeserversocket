try:
    # if this succeeds, it means that we are running inside Nuke
    import nuke
except ImportError:
    # otherwise import the fake nuke api
    from . import _nuke as nuke

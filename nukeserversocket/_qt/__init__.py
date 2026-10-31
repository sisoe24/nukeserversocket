"""Qt binding compatibility: PySide6 (Nuke 16+) with a PySide2 fallback (Nuke 15 and older).

Import Qt names from the submodules, e.g. ``from ._qt.QtWidgets import QWidget``.
"""
try:
    from PySide6 import __version__
except ImportError:
    from PySide2 import __version__  # noqa: F401

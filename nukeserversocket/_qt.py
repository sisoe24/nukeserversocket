"""Qt binding compatibility: PySide6 (Nuke 16+) with a PySide2 fallback (Nuke 15 and older).

Import Qt names straight from here, e.g. ``from ._qt import QWidget``.
"""
# pyright: reportWildcardImportFromLibrary=false
# isort: skip_file
try:
    from PySide6 import __version__
    from PySide6.QtCore import *  # noqa: F401,F403
    from PySide6.QtGui import *  # noqa: F401,F403
    from PySide6.QtWidgets import *  # noqa: F401,F403
    from PySide6.QtNetwork import *  # noqa: F401,F403
except ImportError:
    from PySide2 import __version__  # noqa: F401  # pyright: ignore[reportMissingImports]
    from PySide2.QtCore import *  # noqa: F401,F403  # pyright: ignore[reportMissingImports]
    from PySide2.QtGui import *  # noqa: F401,F403  # pyright: ignore[reportMissingImports]
    from PySide2.QtWidgets import *  # noqa: F401,F403  # pyright: ignore[reportMissingImports]
    from PySide2.QtNetwork import *  # noqa: F401,F403  # pyright: ignore[reportMissingImports]

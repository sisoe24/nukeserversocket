from __future__ import annotations

try:
    from PySide6.QtGui import *  # noqa: F401,F403
except ImportError:
    from PySide2.QtGui import *  # noqa: F401,F403
    from PySide2.QtWidgets import QAction  # noqa: F401  Qt5 location

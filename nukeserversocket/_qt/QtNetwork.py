from __future__ import annotations

try:
    from PySide6.QtNetwork import *  # noqa: F401,F403
except ImportError:
    from PySide2.QtNetwork import *  # noqa: F401,F403

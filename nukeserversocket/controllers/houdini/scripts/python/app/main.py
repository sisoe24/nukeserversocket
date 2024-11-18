"""Nuke-specific plugin for the NukeServerSocket."""
from __future__ import annotations

import traceback
from typing import Optional

from PySide2.QtWidgets import QWidget

from nukeserversocket.main import NukeServerSocket
from nukeserversocket.utils import stdoutIO
from nukeserversocket.received_data import ReceivedData
from nukeserversocket.controllers.base import BaseController


class HoudiniController(BaseController):
    def execute(self, data: ReceivedData) -> str:
        with stdoutIO() as s:
            try:
                exec(data.text, globals())
            except Exception:
                return traceback.format_exc()
            return s.getvalue()


class HoudiniEditor(NukeServerSocket):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(HoudiniController(), parent)

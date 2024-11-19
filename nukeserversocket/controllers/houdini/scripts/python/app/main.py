"""Nuke-specific plugin for the NukeServerSocket."""
from __future__ import annotations

from typing import Optional

from PySide2.QtWidgets import QWidget

from nukeserversocket.main import NukeServerSocket
from nukeserversocket.utils import exec_code
from nukeserversocket.received_data import ReceivedData
from nukeserversocket.controllers.base import BaseController


class HoudiniController(BaseController):
    def execute(self, data: ReceivedData) -> str:
        return exec_code(data.text, data.file)


class HoudiniEditor(NukeServerSocket):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(HoudiniController(), parent)

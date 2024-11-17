"""Nuke-specific plugin for the NukeServerSocket."""
from __future__ import annotations

from nukeserversocket.main import NukeServerSocket
from nukeserversocket.utils import stdoutIO
from nukeserversocket.controllers import BaseController
from nukeserversocket.received_data import ReceivedData


class HoudiniController(BaseController):
    def execute(self, data: ReceivedData) -> str:
        with stdoutIO() as s:
            exec(data.text, globals())
            return s.getvalue()


class HoudiniEditor(NukeServerSocket):
    def __init__(self, parent=None):
        super().__init__(HoudiniController(), parent)

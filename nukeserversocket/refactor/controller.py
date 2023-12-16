from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional

from .received_data import ReceivedData


class BaseController(ABC):

    @abstractmethod
    def execute(self, data: ReceivedData) -> str: ...


C = Callable[[], BaseController]


class Controller:
    _controller: Optional[C] = None

    @classmethod
    def get_instance(cls) -> Optional[C]:
        return cls._controller

    @classmethod
    def set_instance(cls, controller: C) -> None:
        cls._controller = controller

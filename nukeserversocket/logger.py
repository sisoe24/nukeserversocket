from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from logging.handlers import TimedRotatingFileHandler

from .utils import ROOT, cache

if TYPE_CHECKING:
    from .console import NssConsole

PACKAGE_LOG = ROOT / 'logs' / 'nukeserversocket.log'
PACKAGE_LOG.parent.mkdir(parents=True, exist_ok=True)


class ConsoleHandler(logging.Handler):
    def __init__(self, console: NssConsole) -> None:
        super().__init__()
        self.set_name('console')
        self.setLevel(logging.INFO)
        self.setFormatter(
            logging.Formatter(
                '[%(asctime)s] %(levelname)-8s - %(message)s', '%H:%M:%S'
            )
        )
        self._console = console

    def emit(self, record: logging.LogRecord) -> None:
        self._console.write(self.format(record) + '\n')


def _file_handler() -> TimedRotatingFileHandler:

    handler = TimedRotatingFileHandler(
        filename=PACKAGE_LOG,
        when='midnight',
        backupCount=7
    )
    handler.setLevel(logging.DEBUG)
    handler.set_name('file')

    f = '[%(asctime)s] %(levelname)-10s - %(module)s:%(lineno)s - %(message)s'
    handler.setFormatter(logging.Formatter(f))

    return handler


class NssLogger(logging.Logger):
    def __init__(self, name: str = 'nukeserversocket') -> None:
        super().__init__(name)
        self.setLevel(logging.DEBUG)
        self.addHandler(_file_handler())

        self._console = logging.NullHandler()

    @property
    def console(self) -> logging.Handler:
        return self._console

    @console.setter
    def console(self, handler: logging.Handler) -> None:
        self._console = handler
        self.addHandler(self._console)


@cache('logger')
def get_logger() -> NssLogger:
    return NssLogger()

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

if TYPE_CHECKING:
    from .console import NssConsole

PACKAGE_LOG = Path(__file__).parent.parent / 'logs' / 'nukeserversocket.log'


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
        self._console.write(self.format(record) + '\n', record.levelname)


def _file_handler() -> TimedRotatingFileHandler:
    PACKAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

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

        try:
            self.addHandler(_file_handler())
        except OSError:
            # read-only install (e.g. a studio network share): log to the console only
            pass

        self._console = logging.NullHandler()

    @property
    def console(self) -> logging.Handler:
        return self._console

    @console.setter
    def console(self, handler: logging.Handler) -> None:
        self._console = handler
        self.addHandler(self._console)


# Shared by every module so the console handler and the file handler are attached once.
_LOGGER = NssLogger()


def get_logger() -> NssLogger:
    return _LOGGER

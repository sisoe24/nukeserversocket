from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler

from .utils import ROOT

PACKAGE_LOG = ROOT / 'logs' / 'nukeserversocket.log'
PACKAGE_LOG.parent.mkdir(parents=True, exist_ok=True)


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


LOGGER = logging.getLogger('nukeserversocket')
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(_file_handler())

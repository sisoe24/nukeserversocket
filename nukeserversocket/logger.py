from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler

from .utils import ROOT, cache

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


@cache
def get_logger() -> logging.Logger:
    logger = logging.getLogger('nukeserversocket')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_file_handler())
    return logger

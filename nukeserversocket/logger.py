"""Logging module."""
# coding: utf-8

import os
import sys
import logging
import logging.handlers

LOGGER = logging.getLogger('nukeserversocket')
LOGGER.propagate = False
LOGGER.setLevel(logging.DEBUG)


def _formatter_detailed():
    return logging.Formatter(
        '%(levelname)s | %(asctime)s | %(name)s | '
        '%(filename)s.%(funcName)s:%(lineno)s | %(message)s'
    )


def _formatter_console():
    return logging.Formatter(
        '%(levelname)-10s - %(module)s:%(lineno)-5s %(funcName)-15s :: %(message)s'
    )


def _get_path(name):
    logs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(logs_path):
        os.mkdir(logs_path)
    return os.path.join(logs_path, f'{name}.log')


def empty_line(log_file='debug'):
    """Append an empty line in the debug.log fie."""
    with open(_get_path(log_file), 'a+') as file:
        file.write('\n')


def _handler_debug():
    """Init function for the debug handler logger."""
    empty_line()
    debug = logging.handlers.TimedRotatingFileHandler(
        filename=_get_path('debug'), when='W6', backupCount=4
    )
    debug.set_name('debug')
    debug.setLevel(logging.DEBUG)
    debug.setFormatter(_formatter_detailed())
    return debug


def _handler_console():
    """Init function for the console handler logger."""
    console = logging.StreamHandler(stream=sys.stdout)
    console.set_name('console')
    console.setLevel(logging.INFO)
    console.setFormatter(_formatter_console())
    return console


LOGGER.addHandler(_handler_debug())
LOGGER.addHandler(_handler_console())

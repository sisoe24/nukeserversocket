"""Logging module."""
# coding: utf-8

import os
import sys
import logging

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


def set_critical():
    """Init function for the critical handler logger."""
    critical = logging.FileHandler(_get_path('error'), 'w')
    critical.setLevel(logging.ERROR)
    critical.setFormatter(_formatter_detailed())
    critical.set_name('critical')
    return critical


def set_debug():
    """Init function for the debug handler logger."""
    empty_line()
    debug = logging.FileHandler(_get_path('debug'), 'w')
    debug.set_name('debug')
    debug.setLevel(logging.DEBUG)
    debug.setFormatter(_formatter_detailed())
    return debug


def set_console():
    """Init function for the console handler logger."""
    console = logging.StreamHandler(stream=sys.stdout)
    console.set_name('console')
    console.setLevel(logging.INFO)
    console.setFormatter(_formatter_console())
    return console


LOGGER.addHandler(set_debug())
LOGGER.addHandler(set_critical())
LOGGER.addHandler(set_console())

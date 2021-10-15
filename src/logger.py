# coding: utf-8
from __future__ import print_function

import os
import sys
import logging

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')

if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)

LOGGER = logging.getLogger('NukeServerSocket')
LOGGER.propagate = False
LOGGER.setLevel(logging.DEBUG)

DEBUG_FILE = os.path.join(LOG_PATH, 'debug.log')

BASE_FORMAT = logging.Formatter(
    '[%(asctime)s]  %(levelname)-10s %(filename)-25s %(funcName)-25s :: %(message)s',
    "%m-%d %I:%M%p")


def empty_line():
    with open(DEBUG_FILE, 'a+') as file:
        file.write('\n')


def set_critical():
    critical = logging.FileHandler(os.path.join(LOG_PATH, 'errors.log'), 'w')
    critical.setLevel(logging.ERROR)
    critical.setFormatter(BASE_FORMAT)
    critical.set_name('Critical')
    return critical


def set_debug():
    empty_line()
    debug = logging.FileHandler(DEBUG_FILE, 'w')
    debug.set_name('Debug')
    debug.setLevel(logging.DEBUG)
    debug.setFormatter(BASE_FORMAT)
    return debug


def set_console():
    console_format = logging.Formatter(
        '%(name)s %(levelname)-8s %(module)-10s%(funcName)-15sL:%(lineno)-5d :: %(message)s')
    console = logging.StreamHandler(stream=sys.stdout)
    console.set_name('Console')
    console.setLevel(logging.WARNING)
    console.setFormatter(console_format)
    return console


LOGGER.addHandler(set_console())
LOGGER.addHandler(set_critical())
LOGGER.addHandler(set_debug())

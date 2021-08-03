"""Utility module for getting various paths in package."""

from os.path import (
    dirname, abspath
)


def get_src():
    """Return src absolute path."""
    return dirname(dirname(abspath(__file__)))


def get_root():
    """Return package root absolute path."""
    return dirname(get_src())

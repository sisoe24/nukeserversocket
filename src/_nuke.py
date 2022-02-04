"""Fake nuke module to test some functionality when launch app locally."""
# coding: utf-8
from __future__ import print_function

import re
from textwrap import dedent

from PySide2.QtGui import QClipboard


def nodeCopy(string):
    """Copy nodes implementation of equivalent Nukes method."""
    copy_tmp = dedent("""
    set cut_paste_input [stack 0]
    version 13.0 v1
    push $cut_paste_input
    Blur {
    size {{curve x-16 100 x25 1.8 x101 100}}
    name Blur1
    selected true
    xpos -150
    ypos -277
    }
    Blur {
    inputs 0
    name Blur2
    selected true
    xpos -40
    ypos -301
    }
    """).strip()
    if re.match(r'^%.+%$', string):
        clipboard = QClipboard()
        clipboard.setText(copy_tmp)
    else:
        with open(string, 'w') as file:
            file.write(copy_tmp)


def executeInMainThreadWithResult(call, args):
    """Internal function placeholder."""
    return args

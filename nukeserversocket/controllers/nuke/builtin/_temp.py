"""Temporary nodes for built-in tools: the script and the undo history do not change."""
from __future__ import annotations

import uuid
from typing import Iterator, List, Tuple
from contextlib import contextmanager

import nuke

RGB = ['rgba.red', 'rgba.green', 'rgba.blue']


@contextmanager
def temp_nodes(tool: str) -> Iterator[Tuple[str, List[nuke.Node]]]:
    """Yield a unique name prefix and a list; nodes added to the list are deleted on exit.

    Pipelines are told to ignore nodes whose names start with _nss_.
    """
    created: List[nuke.Node] = []
    undo_was_on = not nuke.Undo.disabled()
    nuke.Undo.disable()
    try:
        yield f'_nss_{tool}_{uuid.uuid4().hex[:8]}', created
    finally:
        for node in reversed(created):
            nuke.delete(node)
        if undo_was_on:
            nuke.Undo.enable()


def copy_to_rgb(source: nuke.Node, channels: List[str], name: str) -> nuke.Node:
    """Return a Copy node that puts `channels` (three names) in red, green and blue."""
    copy = nuke.nodes.Copy(name=name, inputs=[source, source])
    for index, channel in enumerate(channels):
        copy[f'from{index}'].setValue(channel)
        copy[f'to{index}'].setValue(RGB[index])
    return copy

"""Temporary nodes for built-in tools: the script and the undo history do not change."""
from __future__ import annotations

import uuid
from typing import List, Tuple, Iterator
from contextlib import contextmanager

import nuke

RGB = ['rgba.red', 'rgba.green', 'rgba.blue']


@contextmanager
def temp_nodes(tool: str, source: nuke.Node) -> Iterator[Tuple[str, nuke.Node]]:
    """Yield a unique name prefix and an Input node that shows `source`.

    Inside the block, new nodes go into one temporary Group, so the artist sees one node
    while the tool runs. The Group is deleted on exit. Pipelines are told to ignore nodes
    whose names start with _nss_.
    """
    name = f'_nss_{tool}_{uuid.uuid4().hex[:8]}'
    undo_was_on = not nuke.Undo.disabled()
    nuke.Undo.disable()
    group = None
    try:
        group = nuke.nodes.Group(name=name)
        with group:
            image = nuke.nodes.Input(name=f'{name}_input')
        group.setInput(0, source)
        with group:
            yield name, image
    finally:
        if group is not None:
            nuke.delete(group)
        if undo_was_on:
            nuke.Undo.enable()


def copy_to_rgb(source: nuke.Node, channels: List[str], name: str) -> nuke.Node:
    """Return a Copy node that puts `channels` (three names) in red, green and blue."""
    copy = nuke.nodes.Copy(name=name, inputs=[source, source])
    for index, channel in enumerate(channels):
        copy[f'from{index}'].setValue(channel)
        copy[f'to{index}'].setValue(RGB[index])
    return copy

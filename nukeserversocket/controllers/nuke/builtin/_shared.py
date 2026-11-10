"""Helpers of the built-in tools.

Their temporary nodes leave the script and the undo history unchanged.
"""
from __future__ import annotations

import uuid
from typing import Any, Iterator
from contextlib import contextmanager

import nuke

from ....tools import ToolError

RGB = ['rgba.red', 'rgba.green', 'rgba.blue']


@contextmanager
def temp_nodes(tool: str, source: nuke.Node) -> Iterator[tuple[str, nuke.Node]]:
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


def copy_to_rgb(source: nuke.Node, channels: list[str], name: str) -> nuke.Node:
    """Return a Copy node that puts `channels` (three names) in red, green and blue."""
    copy = nuke.nodes.Copy(name=name, inputs=[source, source])
    for index, channel in enumerate(channels):
        copy[f'from{index}'].setValue(channel)
        copy[f'to{index}'].setValue(RGB[index])
    return copy


def viewer_info(viewer: nuke.ViewerWindow | None) -> dict[str, Any] | None:
    if viewer is None:
        return None
    node = viewer.node()
    index = viewer.activeInput()
    source = node.input(index) if index is not None else None
    info = {
        'name': node.name(),
        'input': source.fullName() if source else None,
        'frame': nuke.frame(),
        'view': viewer.view(),
        'gain': node['gain'].value(),
        'gamma': node['gamma'].value(),
        'viewer_process': node['viewerProcess'].value(),
    }
    # Nuke 17 and newer
    if hasattr(node, 'getZoomLevel'):
        info['zoom_percent'] = node.getZoomLevel()
    return info


def find_source(node: str, viewer: nuke.ViewerWindow | None) -> nuke.Node:
    if node:
        found = nuke.toNode(node)
        if found is None:
            raise ToolError(f'No node named {node!r}.')
        return found

    if viewer is None:
        raise ToolError('No active Viewer. Pass node, or open a Viewer.')
    index = viewer.activeInput()
    found = viewer.node().input(index) if index is not None else None
    if found is None:
        raise ToolError(f'Nothing is connected to the active input of {viewer.node().name()}. '
                        'Pass node.')
    return found


def pick_channels(source: nuke.Node, channels: str) -> list[str]:
    """Return the channels that `channels` names: rgb, rgba, alpha, a layer or one channel."""
    available = source.channels()
    if not available:
        raise ToolError(f'{source.fullName()} has no image. Is its input connected?')
    picked = {'rgb': RGB, 'rgba': RGB + ['rgba.alpha'], 'alpha': ['rgba.alpha']}.get(channels)
    if picked is None:
        picked = [channels] if channels in available else [
            c for c in available if c.split('.')[0] == channels]
    missing = [c for c in picked if c not in available]
    if missing:
        raise ToolError(f'{source.fullName()} has no {", ".join(missing)}. '
                        f'Channels: {sorted(available)}.')
    if not picked:
        layers = sorted({c.split('.')[0] for c in available})
        raise ToolError(f'{source.fullName()} has no channel or layer {channels!r}. '
                        f'Layers: {layers}.')
    return picked


def source_warnings(source: nuke.Node, frame: int) -> list[str]:
    warnings = []
    if not source.firstFrame() <= frame <= source.lastFrame():
        warnings.append(f'Frame {frame} is outside the frame range of {source.fullName()} '
                        f'({source.firstFrame()}-{source.lastFrame()}).')
    if source.hasError():
        warnings.append(f'{source.fullName()} reports an error.')
    if nuke.root()['proxy'].value():
        warnings.append('Proxy mode is on: the image is rendered at proxy resolution.')
    return warnings

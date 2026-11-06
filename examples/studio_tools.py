"""Example adapters for nss_tools.json.

Each adapter is the only thing a client can run. Keep them safe to call from a
remote client: arguments are JSON values, nothing opens a dialog, nothing reads
the user's selection, and every result is JSON.
"""
from __future__ import annotations

import nuke


def script_info():
    """Describe the open script."""
    root = nuke.root()
    return {
        # root.name() is always 'Root'; the knob holds the path, empty while unsaved
        'script': root['name'].value(),
        'first_frame': int(root['first_frame'].value()),
        'last_frame': int(root['last_frame'].value()),
        'fps': root['fps'].value(),
        'modified': root.modified(),
    }


def list_writes():
    """List the Write nodes and the files they render to."""
    return [
        {'name': node.name(), 'file': node['file'].value(), 'disabled': node['disable'].value()}
        for node in nuke.allNodes('Write')
    ]


def render_write(node, first=None, last=None):
    """Render one Write node by name, over the script range unless a range is given."""
    write = nuke.toNode(node)
    # check by name, never use the selection: the artist may have changed it
    if write is None or write.Class() != 'Write':
        raise ValueError(f'No Write node named {node!r}.')

    root = nuke.root()
    first = int(root['first_frame'].value()) if first is None else first
    last = int(root['last_frame'].value()) if last is None else last
    if first > last:
        raise ValueError(f'first ({first}) is after last ({last}).')

    nuke.execute(write, first, last)
    return {'node': node, 'first': first, 'last': last, 'file': write['file'].value()}

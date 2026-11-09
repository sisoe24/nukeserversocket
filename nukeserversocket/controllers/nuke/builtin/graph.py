"""Describe one group of the node graph, compactly.

Built-in MCP tool nuke_graph. Code running in Nuke can call it too:

    from nukeserversocket.controllers.nuke.builtin.graph import graph
    print(graph(group='Group1'))
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Tuple, Optional
from collections import Counter, OrderedDict

import nuke

from .vision import _viewer_info
from ....tools import Tool, ToolError

MAX_NODES = 200
# a Roto curves knob can be 300,000 characters
MAX_KNOB = 1000
MAX_SNAPSHOTS = 4

# snapshot id -> (group full name, {node full name: fingerprint})
_snapshots: 'OrderedDict[str, Tuple[str, Dict[str, int]]]' = OrderedDict()


def _find_group(group: str) -> nuke.Group:
    if not group:
        return nuke.root()
    found = nuke.toNode(group)
    if found is None:
        raise ToolError(f'No node named {group!r}.')
    if not isinstance(found, nuke.Group):
        raise ToolError(f'{group} is a {found.Class()}, not a Group.')
    return found


def _inputs(node: nuke.Node) -> List[Any]:
    return [i.fullName() if i else None for i in (node.input(n) for n in range(node.inputs()))]


def _knob_values(node: nuke.Node) -> Dict[str, str]:
    # without WRITE_ALL, the Node tab (label, disable, tile_color) is left out;
    # without TO_SCRIPT, writeKnobs gives only the names
    names = node.writeKnobs(nuke.WRITE_NON_DEFAULT_ONLY | nuke.WRITE_ALL).split()
    return {name: node[name].toScript() for name in names
            if name not in ('name', 'selected') and node.knob(name) is not None}


def _fingerprint(node: nuke.Node) -> int:
    # position included, so a moved node counts as changed
    return hash((tuple(_knob_values(node).items()), tuple(_inputs(node))))


def _shown(node: nuke.Node, name: str) -> bool:
    # UI state, not the comp: position, hidden knobs, the Viewer toolbar; read others with code
    knob = node[name]
    return not (name in ('xpos', 'ypos') or 'toolbar' in name or 'toolbox' in name
                or knob.getFlag(nuke.INVISIBLE) or not knob.visible())


def _describe(node: nuke.Node, error: bool) -> Dict[str, Any]:
    # the reply's viewer field already has what matters of a Viewer
    values = {} if node.Class() == 'Viewer' else _knob_values(node)
    knobs = {name: value if len(value) <= MAX_KNOB else f'<cut: {len(value)} characters>'
             for name, value in values.items() if _shown(node, name)}
    entry = {'name': node.fullName(), 'class': node.Class(), 'inputs': _inputs(node),
             'knobs': knobs}
    if error:
        entry['error'] = True
    if isinstance(node, nuke.Group):
        entry['children'] = len(node.nodes())
    return entry


def _script_info() -> Dict[str, Any]:
    root = nuke.root()
    fmt = root.format()
    info = {
        'path': root['name'].value(),
        'modified': root.modified(),
        'frame': nuke.frame(),
        'first_frame': int(root['first_frame'].value()),
        'last_frame': int(root['last_frame'].value()),
        'fps': root['fps'].value(),
        'format': {'name': fmt.name(), 'width': fmt.width(), 'height': fmt.height(),
                   'pixel_aspect': fmt.pixelAspect()},
        'proxy': bool(root['proxy'].value()),
        'views': nuke.views(),
    }
    for knob in ('colorManagement', 'OCIO_config'):
        if knob in root.knobs():
            info[knob] = root[knob].value()
    return info


def graph(group: str = '', max_nodes: int = MAX_NODES, since: str = '',
          classes: Optional[List[str]] = None) -> Dict[str, Any]:
    """Describe the direct children of `group` (the root by default)."""
    if not 1 <= max_nodes <= 1000:
        raise ToolError(f'max_nodes must be 1 to 1000, got {max_nodes}.')
    if classes is not None and not all(isinstance(c, str) for c in classes):
        raise ToolError('classes must be a list of class names, for example ["Read"].')

    parent = _find_group(group)
    nodes = parent.nodes()
    # first: hasError validates a new node, and validation can fill knobs (Read, Text2)
    errors = {n.fullName(): n.hasError() for n in nodes}
    fingerprints = {n.fullName(): _fingerprint(n) for n in nodes}

    reply: Dict[str, Any] = {
        'script': _script_info(),
        'viewer': _viewer_info(nuke.activeViewer()),
        'selected': [n.fullName() for n in nuke.selectedNodes()],
        'group': parent.fullName() if group else 'root',
    }

    warnings = []
    if since:
        previous = _snapshots.get(since)
        if previous is None or previous[0] != reply['group']:
            warnings.append(f'Unknown snapshot {since!r} for this group: full graph listed.')
        else:
            old = previous[1]
            nodes = [n for n in nodes if old.get(n.fullName()) != fingerprints[n.fullName()]]
            reply['removed'] = [name for name in old if name not in fingerprints]

    if classes:
        nodes = [n for n in nodes if n.Class() in classes]
    reply['nodes'] = [_describe(n, errors[n.fullName()]) for n in nodes[:max_nodes]]
    if len(nodes) > max_nodes:
        counts = Counter(n.Class() for n in nodes).most_common(10)
        listed = ', '.join(f'{name} {count}' for name, count in counts)
        reply['truncated'] = (f'{max_nodes} of {len(nodes)} nodes listed. Most common classes: '
                              f'{listed}. Use classes to list only some, or raise max_nodes.')

    snapshot = uuid.uuid4().hex[:8]
    _snapshots[snapshot] = (reply['group'], fingerprints)
    while len(_snapshots) > MAX_SNAPSHOTS:
        _snapshots.popitem(last=False)
    reply['snapshot'] = snapshot
    if warnings:
        reply['warnings'] = warnings
    return reply


GRAPH_TOOL = Tool(
    name='nuke_graph',
    description=(
        'Read the node graph: the direct children of one group (the root by default), with '
        'their class, inputs and non-default knobs. Also the script settings, the Viewer and '
        'the selection. Use it first to learn a script, and after a change to see what '
        'changed.\n\n'
        '- inputs: input node names in order; null is an empty input. For a Merge2, the '
        'order is B, A, mask.\n'
        '- knobs: values in .nk syntax. Hidden knobs, toolbar settings and Viewer knobs are '
        'left out. A value over 1000 characters shows as "<cut: N characters>". Read '
        'anything left out with code if you need it.\n'
        '- error appears only when the node has an error. children is the node count of a '
        'Group; call again with group set to its name to look inside.\n'
        '- since: pass the snapshot of an earlier reply to list only the nodes that changed, '
        'were added (nodes) or were deleted (removed) since then. A moved node counts as '
        'changed; a renamed node as removed and added.\n'
        '- classes: list only nodes of these classes, for example ["Read", "Write"]. Use it '
        'on a big script instead of raising max_nodes.\n'
        '- The selection tells you what the artist means by "this". Do not change it.'
    ),
    input_schema={
        'type': 'object',
        'properties': {
            'group': {'type': 'string',
                      'description': 'Full name of a Group, for example "Group1". Default: root.'},
            'max_nodes': {'type': 'integer',
                          'description': f'1 to 1000. Default {MAX_NODES}.'},
            'since': {'type': 'string', 'description': 'snapshot from an earlier reply.'},
            'classes': {'type': 'array', 'items': {'type': 'string'},
                        'description': 'Node classes to list. Default: all.'},
        },
    },
    function=graph,
    annotations={'title': 'Read the Nuke node graph', 'readOnlyHint': True,
                 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False},
)

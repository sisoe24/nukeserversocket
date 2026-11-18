"""Focus boxes: nodes that mark the region of the image an agent should look at.

The artist creates one from the Viewer menu (Mark Region for Agent) and drags its handles.
nuke_vision and nuke_stats crop to it when the agent passes its name as focus.
"""
from __future__ import annotations

import nuke

from ....tools import ToolError

MARKER = 'nss_focus'


def _disabled(node: nuke.Node) -> bool:
    # a NoOp has no disable knob: focus boxes add their own
    knob = node.knob('disable')
    return knob is not None and bool(knob.value())


def focus_boxes() -> list[str]:
    """Return the full names of the focus boxes that are not disabled."""
    return [node.fullName() for node in nuke.allNodes(recurseGroups=True, group=nuke.root())
            if node.knob(MARKER) is not None and not _disabled(node)]


def focus_crop(name: str, frame: int) -> list[float]:
    """Return the area of focus box `name` at `frame` as a crop: [x, y, width, height]."""
    # full names start at the root, whatever group the code runs in
    with nuke.root():
        node = nuke.toNode(name)
    if node is None or node.knob(MARKER) is None:
        raise ToolError(f'{name!r} is not a focus box. Focus boxes: {focus_boxes()}.')
    if _disabled(node):
        raise ToolError(f'{name} is disabled.')

    x, y, right, top = node['area'].valueAt(frame)
    if right <= x or top <= y:
        raise ToolError(f'{name} has no area at frame {frame}.')
    return [x, y, right - x, top - y]


def create_focus_box() -> nuke.Node:
    """Create a focus box over the middle of the Viewer's image and open its panel."""
    viewer = nuke.activeViewer()
    index = viewer.activeInput() if viewer else None
    source = viewer.node().input(index) if index is not None else None
    fmt = source.format() if source else nuke.root().format()

    number = 1
    while nuke.toNode(f'nssFocus{number}'):
        number += 1

    # a NoOp: nothing renders, and the panel shows only the box and disable.
    # nuke.nodes does not connect the new node to the selection
    box = nuke.nodes.NoOp(name=f'nssFocus{number}')
    box.addKnob(nuke.Tab_Knob('focus_box', 'Focus Box'))
    box.addKnob(nuke.Text_Knob('about', '', 'Region the AI agent looks at. '
                               'Drag the box in the Viewer.'))
    area = nuke.BBox_Knob('area', 'area')
    box.addKnob(area)
    disable = nuke.Boolean_Knob('disable', 'disable')
    disable.setFlag(nuke.STARTLINE)
    box.addKnob(disable)
    marker = nuke.Boolean_Knob(MARKER, '')
    marker.setFlag(nuke.INVISIBLE)
    box.addKnob(marker)
    marker.setValue(True)

    width, height = fmt.width(), fmt.height()
    area.setValue([width / 4, height / 4, width * 3 / 4, height * 3 / 4])
    if source:
        box.setXYpos(source.xpos() + 150, source.ypos())

    # the handles show in the Viewer while the panel is open
    nuke.show(box)
    return box

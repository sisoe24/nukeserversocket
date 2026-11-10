"""Render one frame of a node to a JPEG, with the colors the Viewer shows.

Built-in MCP tool nuke_vision. Code running in Nuke can call it too:

    from nukeserversocket.controllers.nuke.builtin.vision import vision
    image = vision('Grade1', frame=1001)
    print(image.text)
    with open('/tmp/grade1.jpg', 'wb') as f:
        f.write(image.data)
"""
from __future__ import annotations

import os
import re
import json
import tempfile
from typing import Any

import nuke

from ._shared import (RGB, temp_nodes, viewer_info, copy_to_rgb, find_source,
                      pick_channels, source_warnings)
from ....tools import Tool, Image, ToolError

DEFAULT_SIZE = 768


def _set_display(write: nuke.Node, viewer_process: str | None) -> str:
    """Use the Viewer's display transform; return what was set."""
    # OCIO viewer processes read "<view> (<display>)"
    match = re.match(r'(.+) \((.+)\)$', viewer_process or '')
    if match and 'transformType' in write.knobs():
        view, display = match.groups()
        if display in write['display'].values() and view in write['view'].values():
            write['transformType'].setValue('display')
            write['display'].setValue(display)
            write['view'].setValue(view)
            return f'display {display}, view {view}'

    # values read "name\tfamily/name" with OCIO
    names = [value.split('\t')[0] for value in write['colorspace'].values()]
    if viewer_process in names:
        write['colorspace'].setValue(viewer_process)
        return f'colorspace {viewer_process}'
    return f'colorspace {write["colorspace"].value()} (Write default, no Viewer transform found)'


def _warnings(source: nuke.Node, shown: nuke.Node, frame: int, view: str,
              region: list[float]) -> list[str]:
    warnings = source_warnings(source, frame)

    # the render warmed the cache, so these samples are free
    x, y, r, t = region
    points = [(x + (r - x) * (i + 0.5) / 5, y + (t - y) * (j + 0.5) / 5)
              for i in range(5) for j in range(5)]
    colors = {tuple(round(shown.sample(c, px, py, frame=frame), 4)
                    for c in RGB) for px, py in points}
    if len(colors) == 1:
        warnings.append(f'The image looks like a single color {list(colors.pop())} '
                        f'({len(points)} samples, before the display transform).')
    return warnings


def vision(node: str = '', frame: int | None = None, view: str = '', channels: str = 'rgb',
           crop: list[float] | None = None, size: int = DEFAULT_SIZE) -> Image:
    """Render one frame of `node` to a JPEG, with its metadata as JSON text."""
    if not 64 <= size <= 4096:
        raise ToolError(f'size must be 64 to 4096 pixels, got {size}.')

    viewer = nuke.activeViewer()
    source = find_source(node, viewer)
    frame = nuke.frame() if frame is None else frame
    view = view or (viewer.view() if viewer else nuke.views()[0])
    if view not in nuke.views():
        raise ToolError(f'No view {view!r}. Views: {nuke.views()}.')
    # three channels to show as red, green and blue: a two-channel layer, e.g. motion
    # vectors, shows its second channel twice
    picked = pick_channels(source, channels)[:3]
    shown_channels = (picked + picked[-1:] * 2)[:3]

    fmt = source.format()
    if crop is not None:
        if len(crop) != 4 or crop[2] <= 0 or crop[3] <= 0:
            raise ToolError('crop must be [x, y, width, height] with a positive width and height.')
        region = [crop[0], crop[1], crop[0] + crop[2], crop[1] + crop[3]]
    else:
        region = [0, 0, fmt.width(), fmt.height()]

    aspect = fmt.pixelAspect()
    width, height = (region[2] - region[0]) * aspect, region[3] - region[1]
    scale = size / max(width, height)
    if crop is None:
        # never enlarge a whole frame; a crop is enlarged on purpose, to see detail
        scale = min(1.0, scale)

    fd, path = tempfile.mkstemp(prefix='nss_vision_', suffix='.jpg')
    os.close(fd)

    try:
        with temp_nodes('vision', source) as (name, last):
            if shown_channels != RGB:
                last = copy_to_rgb(last, shown_channels, f'{name}_copy')
            shown = last

            if crop is not None:
                last = nuke.nodes.Crop(name=f'{name}_crop', inputs=[last], reformat=True)
                last['box'].setValue(region)

            if scale != 1 or aspect != 1:
                last = nuke.nodes.Reformat(name=f'{name}_reformat', inputs=[last], type='scale',
                                           filter='Impulse' if scale > 1 else 'Cubic')
                last['scale'].setValue([scale * aspect, scale])

            file = path.replace('\\', '/')
            # proxy: without it, a render in proxy mode fails
            write = nuke.nodes.Write(name=f'{name}_write', inputs=[last], file=file, proxy=file,
                                     file_type='jpeg', channels='rgb')
            display = _set_display(write,
                                   viewer.node()['viewerProcess'].value() if viewer else None)

            try:
                nuke.execute(write, frame, frame, 1, views=[view])
            except RuntimeError as e:
                raise ToolError(f'Cannot render {source.fullName()} at frame {frame}: '
                                f'{e}') from None
            with open(path, 'rb') as f:
                data = f.read()

            warnings = _warnings(source, shown, frame, view, region)
    finally:
        os.remove(path)

    bbox = source.bbox()
    image_width, image_height = round(width * scale), round(height * scale)
    sx, sy = scale * aspect, scale
    metadata = json.dumps({
        'node': source.fullName(),
        'class': source.Class(),
        'frame': frame,
        'view': view,
        'channels': shown_channels,
        'display': display,
        'format': {'name': fmt.name(), 'width': fmt.width(), 'height': fmt.height(),
                   'pixel_aspect': aspect},
        'bbox': [bbox.x(), bbox.y(), bbox.x() + bbox.w(), bbox.y() + bbox.h()],
        'region': region,
        'image': [image_width, image_height],
        # Nuke puts y = 0 at the bottom, the image at the top
        'to_nuke': f'nuke_x = {region[0]:g} + image_x / {sx:g}; '
                   f'nuke_y = {region[3]:g} - image_y / {sy:g}',
        'warnings': warnings,
        'viewer': viewer_info(viewer),
    })
    return Image(data, text=metadata)


VISION_TOOL = Tool(
    name='nuke_vision',
    description=(
        'See an image in Nuke: render one frame of a node to a JPEG, with the colors the '
        "artist's Viewer shows. By default it renders the node feeding the active Viewer "
        'input, at the current frame and view, with the long edge at most 768 pixels. Use it '
        'to check the result of a change, or to see what the artist means by "this".\n\n'
        'The reply is JSON metadata, then the image. The metadata has the format, bounding '
        'box, the region shown, a formula from image pixels to Nuke coordinates (Nuke puts '
        'y = 0 at the bottom), warnings (frame outside the range, single-color image, proxy '
        'mode) and what the Viewer shows.\n\n'
        '- crop: [x, y, width, height] in Nuke pixels, enlarged to size, to see a detail.\n'
        '- channels: "alpha", a layer such as "depth" or "diffuse", or one channel such as '
        '"depth.Z", shown as rgb or greyscale.\n'
        "- The image has the Viewer's display transform, not its gain, gamma, wipe or "
        'overlays.\n'
        '- For min, max, mean or NaN counts, use nuke_stats. For the value at a few points, '
        'call node.sample() with nuke_execute_code right after: the render warmed the cache, '
        'so it is instant.\n'
        '- Nuke is busy until the render finishes. A temporary Write node renders the frame '
        'and is deleted; the scene, the Viewer and the undo history do not change.'
    ),
    input_schema={
        'type': 'object',
        'properties': {
            'node': {'type': 'string',
                     'description': 'Node to render. Default: the node feeding the active '
                                    'Viewer input.'},
            'frame': {'type': 'integer', 'description': 'Default: the current frame.'},
            'view': {'type': 'string', 'description': "Default: the Viewer's view."},
            'channels': {'type': 'string',
                         'description': 'Default "rgb". Or "alpha", a layer, or a channel.'},
            'crop': {'type': 'array', 'items': {'type': 'number'},
                     'description': '[x, y, width, height] in Nuke pixels, y up.'},
            'size': {'type': 'integer',
                     'description': f'Long edge in pixels, 64 to 4096. Default {DEFAULT_SIZE}. '
                                    'Most clients scale images over 1568 down.'},
        },
    },
    function=vision,
    annotations={'title': 'See an image in Nuke', 'readOnlyHint': True,
                 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False},
)

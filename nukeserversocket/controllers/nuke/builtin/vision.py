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
import inspect
import tempfile
from typing import Any

import nuke

from ._shared import (RGB, bbox, pick_view, temp_nodes, viewer_info, copy_to_rgb,
                      find_source, pick_channels, source_warnings)
from ....tools import Tool, Image, ToolError

DEFAULT_SIZE = 768

# the samples that tell a single-color image: a grid of GRID x GRID points
GRID = 5

# Viewer processes of Nuke color management with another name on the Write
DISPLAY_ALIASES = {'None': 'linear', 'rec1886': 'BT1886'}


def _region(fmt: nuke.Format, crop: list[float] | None) -> list[float]:
    """Return the region to render as [x, y, right, top]: the crop, or the whole format.

    Unlike nuke_stats, fractions stay: a crop can zoom past one pixel.
    """
    if crop is None:
        return [0, 0, fmt.width(), fmt.height()]

    if len(crop) != 4 or crop[2] <= 0 or crop[3] <= 0:
        raise ToolError('crop must be [x, y, width, height] with a positive width and height.')

    x, y, width, height = crop
    return [x, y, x + width, y + height]


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
    colorspace = DISPLAY_ALIASES.get(viewer_process or '', viewer_process)
    if colorspace in names:
        write['colorspace'].setValue(colorspace)
        return f'colorspace {colorspace}'

    default = write['colorspace'].value()
    return f'colorspace {default} (Write default, no Viewer transform found)'


def _jpeg_size(data: bytes) -> tuple[int, int]:
    """Return the width and height of a JPEG, from its start-of-frame segment."""
    i = 2
    while i + 9 <= len(data):
        marker, length = data[i + 1], int.from_bytes(data[i + 2:i + 4], 'big')
        # SOF0 to SOF15, except DHT (C4), JPG (C8) and DAC (CC)
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height = int.from_bytes(data[i + 5:i + 7], 'big')
            width = int.from_bytes(data[i + 7:i + 9], 'big')
            return width, height
        i += 2 + length
    raise ToolError('The rendered JPEG has no size.')


def _single_color(shown: nuke.Node, frame: int, region: list[float]) -> str | None:
    """Return a warning when a grid of samples finds one color only."""
    x, y, right, top = region
    width, height = right - x, top - y

    colors = set()
    for i in range(GRID):
        for j in range(GRID):
            px = x + width * (i + 0.5) / GRID
            py = y + height * (j + 0.5) / GRID
            # the render warmed the cache, so these samples are free
            color = tuple(round(shown.sample(c, px, py, frame=frame), 4) for c in RGB)
            colors.add(color)

    if len(colors) > 1:
        return None
    return (f'The image looks like a single color {list(colors.pop())} '
            f'({GRID * GRID} samples, before the display transform).')


def vision(
    node: str = '',
    frame: int | None = None,
    view: str = '',
    channels: str = 'rgb',
    crop: list[float] | None = None,
    size: int = DEFAULT_SIZE,
) -> Image:
    """Render one frame of `node` to a JPEG, with its metadata as JSON text."""
    if not 64 <= size <= 4096:
        raise ToolError(f'size must be 64 to 4096 pixels, got {size}.')

    viewer = nuke.activeViewer()
    source = find_source(node, viewer)
    frame = nuke.frame() if frame is None else frame

    view = pick_view(view, viewer)

    # three channels to show as red, green and blue; a two-channel layer, such as motion
    # vectors, shows its second channel twice
    picked = pick_channels(source, channels)[:3]
    shown_channels = (picked + picked[-1:] * 2)[:3]

    fmt = source.format()
    region = _region(fmt, crop)
    aspect = fmt.pixelAspect()
    width = (region[2] - region[0]) * aspect
    height = region[3] - region[1]

    scale = size / max(width, height)
    if crop is None:
        # never enlarge a whole frame; a crop is enlarged on purpose, to see detail
        scale = min(1.0, scale)

    viewer_process = viewer.node()['viewerProcess'].value() if viewer else None
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
                last = nuke.nodes.Reformat(
                    name=f'{name}_reformat',
                    inputs=[last],
                    type='scale',
                    filter='Impulse' if scale > 1 else 'Cubic',
                )
                last['scale'].setValue([scale * aspect, scale])

            file = path.replace('\\', '/')
            write = nuke.nodes.Write(
                name=f'{name}_write',
                inputs=[last],
                file=file,
                # without a proxy file, a render in proxy mode fails
                proxy=file,
                file_type='jpeg',
                channels='rgb',
            )
            display = _set_display(write, viewer_process)

            try:
                nuke.execute(write, frame, frame, 1, views=[view])
            except RuntimeError as e:
                message = f'Cannot render {source.fullName()} at frame {frame}: {e}'
                raise ToolError(message) from None

            with open(path, 'rb') as f:
                data = f.read()

            warnings = source_warnings(source, frame)
            single_color = _single_color(shown, frame, region)
            if single_color:
                warnings.append(single_color)
    finally:
        os.remove(path)

    # in proxy mode the JPEG is smaller than the scale asks: measure it
    image_width, image_height = _jpeg_size(data)
    scale_x = image_width / (region[2] - region[0])
    scale_y = image_height / (region[3] - region[1])
    metadata: dict[str, Any] = {
        'node': source.fullName(),
        'class': source.Class(),
        'frame': frame,
        'view': view,
        'channels': shown_channels,
        'display': display,
        'format': {
            'name': fmt.name(),
            'width': fmt.width(),
            'height': fmt.height(),
            'pixel_aspect': aspect,
        },
        'bbox': bbox(source),
        'region': region,
        'image': [image_width, image_height],
        # Nuke puts y = 0 at the bottom, the image at the top
        'to_nuke': (f'nuke_x = {region[0]:g} + image_x / {scale_x:g}; '
                    f'nuke_y = {region[3]:g} - image_y / {scale_y:g}'),
        'warnings': warnings,
        'viewer': viewer_info(viewer),
    }
    return Image(data, text=json.dumps(metadata))


DESCRIPTION = inspect.cleandoc(f"""
    See an image in Nuke: render one frame of a node to a JPEG, with the colors the artist's
    Viewer shows. By default it renders the node feeding the active Viewer input, at the
    current frame and view, with the long edge at most {DEFAULT_SIZE} pixels. Use it to check
    the result of a change, or to see what the artist means by "this".

    The reply is JSON metadata, then the image. The metadata has the format, bounding box,
    the region shown, a formula from image pixels to Nuke coordinates (Nuke puts y = 0 at the
    bottom), warnings (frame outside the range, single-color image, proxy mode) and what the
    Viewer shows.

    - crop: [x, y, width, height] in Nuke pixels, enlarged to size, to see a detail.
    - channels: "alpha", a layer such as "depth" or "diffuse", or one channel such as
      "depth.Z", shown as rgb or greyscale.
    - The image has the Viewer's display transform, not its gain, gamma, wipe or overlays.
    - For min, max, mean or NaN counts, use nuke_stats. For the value at a few points, call
      node.sample() with nuke_execute_code right after: the render warmed the cache, so it is
      instant.
    - Nuke is busy until the render finishes. Temporary nodes render the frame and are
      deleted; the scene, the Viewer and the undo history do not change.
""")

VISION_TOOL = Tool(
    name='nuke_vision',
    description=DESCRIPTION,
    input_schema={
        'type': 'object',
        'properties': {
            'node': {
                'type': 'string',
                'description': 'Node to render. Default: the node feeding the active Viewer '
                               'input.',
            },
            'frame': {
                'type': 'integer',
                'description': 'Default: the current frame.',
            },
            'view': {
                'type': 'string',
                'description': "Default: the Viewer's view.",
            },
            'channels': {
                'type': 'string',
                'description': 'Default "rgb". Or "alpha", a layer, or a channel.',
            },
            'crop': {
                'type': 'array',
                'items': {'type': 'number'},
                'description': '[x, y, width, height] in Nuke pixels, y up.',
            },
            'size': {
                'type': 'integer',
                'description': f'Long edge in pixels, 64 to 4096. Default {DEFAULT_SIZE}. '
                               'Most clients scale images over 1568 down.',
            },
        },
    },
    function=vision,
    annotations={
        'title': 'See an image in Nuke',
        'readOnlyHint': True,
        'destructiveHint': False,
        'idempotentHint': True,
        'openWorldHint': False,
    },
)

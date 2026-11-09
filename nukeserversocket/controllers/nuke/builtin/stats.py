"""Exact pixel statistics of one frame of a node: min, max, mean, NaN and infinity counts.

Built-in MCP tool nuke_stats. Code running in Nuke can call it too:

    from nukeserversocket.controllers.nuke.builtin.stats import stats
    print(stats('Grade1', frame=1001, channels='rgba'))

CurveTool reads every pixel, so a single hot pixel is found. Sampling a grid of points
misses it.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import nuke

from .vision import _find_source, _source_warnings
from ._temp import RGB, temp_nodes, copy_to_rgb
from ....tools import Tool, ToolError

MAX_CHANNELS = 8
NOT_FINITE = 'isnan(r)||isinf(r)'


def _pick_channels(source: nuke.Node, channels: str) -> List[str]:
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
    if len(picked) > MAX_CHANNELS:
        raise ToolError(f'{channels!r} has {len(picked)} channels; at most {MAX_CHANNELS}.')
    return picked


def _channel_stats(source: nuke.Node, channel: str, region: List[int], pixels: int,
                   frame: int, view: str, name: str, created: List[nuke.Node]) -> Dict[str, Any]:
    def node(cls, **knobs):
        new = getattr(nuke.nodes, cls)(name=f'{name}_{len(created)}', **knobs)
        created.append(new)
        return new

    def run(image, operation):
        curve = node('CurveTool', inputs=[image], operation=operation)
        curve['ROI'].setValue(region)
        try:
            nuke.execute(curve, frame, frame, 1, views=[view])
        except RuntimeError as e:
            raise ToolError(f'Cannot read {source.fullName()} at frame {frame}: {e}') from None
        return curve

    shown = copy_to_rgb(source, [channel] * 3, f'{name}_{len(created)}')
    created.append(shown)

    # one pass: NaN in red, infinity in green, finite values (0 elsewhere) in blue
    counts = node('Expression', inputs=[shown], expr0='isnan(r)?1:0', expr1='isinf(r)?1:0',
                  expr2=f'{NOT_FINITE}?0:r')
    average = run(counts, 'Avg Intensities')['intensitydata'].value()
    nan, inf = round(average[0] * pixels), round(average[1] * pixels)
    finite = pixels - nan - inf
    result: Dict[str, Any] = {'min': None, 'min_at': None, 'max': None, 'max_at': None,
                              'mean': average[2] * pixels / finite if finite else None,
                              'nan': nan, 'inf': inf}
    if not finite:
        return result

    # Max Luma Pixel skips NaN but takes infinity as the maximum: push non-finite values out
    high = low = shown
    if nan or inf:
        high = node('Expression', inputs=[shown], **{f'expr{i}': f'{NOT_FINITE}?-1e30:r'
                                                     for i in range(3)})
        low = node('Expression', inputs=[shown], **{f'expr{i}': f'{NOT_FINITE}?1e30:r'
                                                    for i in range(3)})
    brightest = run(high, 'Max Luma Pixel')
    darkest = brightest if low is high else run(low, 'Max Luma Pixel')
    result.update({
        'max': brightest['maxlumapixvalue'].value()[0],
        'max_at': [int(v) for v in brightest['maxlumapixdata'].value()],
        'min': darkest['minlumapixvalue'].value()[0],
        'min_at': [int(v) for v in darkest['minlumapixdata'].value()],
    })
    return result


def stats(node: str = '', frame: Optional[int] = None, view: str = '', channels: str = 'rgb',
          crop: Optional[List[float]] = None) -> Dict[str, Any]:
    """Return exact statistics of one frame of `node`, per channel."""
    viewer = nuke.activeViewer()
    source = _find_source(node, viewer)
    frame = nuke.frame() if frame is None else frame
    view = view or (viewer.view() if viewer else nuke.views()[0])
    if view not in nuke.views():
        raise ToolError(f'No view {view!r}. Views: {nuke.views()}.')
    picked = _pick_channels(source, channels)

    fmt = source.format()
    if crop is not None:
        if len(crop) != 4 or crop[2] < 1 or crop[3] < 1:
            raise ToolError('crop must be [x, y, width, height] with a width and height of '
                            'at least 1.')
        x, y = round(crop[0]), round(crop[1])
        region = [x, y, x + round(crop[2]), y + round(crop[3])]
    else:
        region = [0, 0, fmt.width(), fmt.height()]
    pixels = (region[2] - region[0]) * (region[3] - region[1])

    with temp_nodes('stats') as (name, created):
        per_channel = {channel: _channel_stats(source, channel, region, pixels, frame, view,
                                               name, created)
                       for channel in picked}

    warnings = _source_warnings(source, frame)
    box = source.bbox()
    bbox = [box.x(), box.y(), box.x() + box.w(), box.y() + box.h()]
    if bbox[0] > region[0] or bbox[1] > region[1] or bbox[2] < region[2] or bbox[3] < region[3]:
        warnings.append(f'The bounding box {bbox} does not cover the region. Outside it, Nuke '
                        'repeats the edge pixels, and they are in these numbers.')

    return {
        'node': source.fullName(),
        'class': source.Class(),
        'frame': frame,
        'view': view,
        'region': region,
        'pixels': pixels,
        'channels': per_channel,
        'warnings': warnings,
    }


STATS_TOOL = Tool(
    name='nuke_stats',
    description=(
        'Measure an image in Nuke: exact min, max and mean of each channel over one frame of '
        'a node, with the pixel position of the min and max, and the count of NaN and '
        'infinite pixels. It reads every pixel, so it finds a single hot or bad pixel. By '
        'default it measures the node feeding the active Viewer input, at the current frame, '
        'over the whole format. Use it to check clipping, black levels, NaN, or whether two '
        'images match; use nuke_vision to see the image.\n\n'
        '- Values are before the display transform, as stored in Nuke.\n'
        '- min, max and mean count only finite pixels. They are null when no pixel is '
        'finite.\n'
        '- Positions are [x, y] in Nuke pixels, y = 0 at the bottom.\n'
        '- crop: [x, y, width, height] in Nuke pixels.\n'
        '- Nuke is busy while it computes the frame. Temporary nodes do the work and are '
        'deleted; the scene and the undo history do not change.'
    ),
    input_schema={
        'type': 'object',
        'properties': {
            'node': {'type': 'string',
                     'description': 'Node to measure. Default: the node feeding the active '
                                    'Viewer input.'},
            'frame': {'type': 'integer', 'description': 'Default: the current frame.'},
            'view': {'type': 'string', 'description': "Default: the Viewer's view."},
            'channels': {'type': 'string',
                         'description': 'Default "rgb". Or "rgba", "alpha", a layer such as '
                                        f'"depth", or one channel. At most {MAX_CHANNELS} '
                                        'channels.'},
            'crop': {'type': 'array', 'items': {'type': 'number'},
                     'description': '[x, y, width, height] in Nuke pixels, y up.'},
        },
    },
    function=stats,
    annotations={'title': 'Measure an image in Nuke', 'readOnlyHint': True,
                 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False},
)

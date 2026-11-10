"""Exact pixel statistics of one frame of a node: min, max, mean, NaN and infinity counts.

Built-in MCP tool nuke_stats. Code running in Nuke can call it too:

    from nukeserversocket.controllers.nuke.builtin.stats import stats
    print(stats('Grade1', frame=1001, channels='rgba'))

CurveTool reads every pixel, so a single hot pixel is found. Sampling a grid of points
misses it.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import nuke

from .vision import _find_source, _source_warnings
from ._temp import RGB, temp_nodes, copy_to_rgb
from ....tools import Tool, ToolError

MAX_CHANNELS = 8
NOT_FINITE = 'isnan(r)||isinf(r)'
# seconds; the bridge waits TIMEOUT for nuke_stats, whatever its --timeout
TIME_LIMIT = 40.0
TIMEOUT = 60.0
MAX_BAD_FRAMES = 10


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


def _channel_curves(image: nuke.Node, channel: str, region: List[int], over: Optional[float],
                    name: str) -> Dict[str, nuke.Node]:
    """Make the CurveTools that measure one channel, in the current group."""
    # pipelines ignore nodes named _nss_*, so every node keeps the prefix
    prefix = f'{name}_{channel.replace(".", "_")}'
    made = []

    def node(cls, **knobs):
        made.append(getattr(nuke.nodes, cls)(name=f'{prefix}_{len(made)}', **knobs))
        return made[-1]

    def curve(image, operation):
        tool = node('CurveTool', inputs=[image], operation=operation)
        tool['ROI'].setValue(region)
        return tool

    shown = copy_to_rgb(image, [channel] * 3, f'{prefix}_copy')
    # one pass: NaN in red, infinity in green, finite values (0 elsewhere) in blue
    counts = node('Expression', inputs=[shown], expr0='isnan(r)?1:0', expr1='isinf(r)?1:0',
                  expr2=f'{NOT_FINITE}?0:r')
    # Max Luma Pixel skips NaN but takes infinity as the maximum: push non-finite values out
    high = node('Expression', inputs=[shown], **{f'expr{i}': f'{NOT_FINITE}?-1e30:r'
                                                 for i in range(3)})
    low = node('Expression', inputs=[shown], **{f'expr{i}': f'{NOT_FINITE}?1e30:r'
                                                for i in range(3)})
    curves = {'counts': curve(counts, 'Avg Intensities'),
              'high': curve(high, 'Max Luma Pixel'),
              'low': curve(low, 'Max Luma Pixel')}
    if over is not None:
        above = node('Expression', inputs=[shown], expr0=f'r>={over!r}?1:0', expr1='0',
                     expr2='0')
        curves['over'] = curve(above, 'Avg Intensities')
    return curves


def _measure(curves: Dict[str, nuke.Node], pixels: int, first: int, last: int,
             view: str) -> Dict[int, Dict[str, Any]]:
    """Statistics of one channel for each frame from first to last.

    Each pass runs once over the whole range: in the GUI, every execute opens the progress
    dialog and moves the timeline. Every frame costs the same, so the first frame tells how
    many fit in the time limit.
    """
    def at(key, knob, frame, size):
        # a CurveTool run on several frames keys each one; in Nuke 17, value() reads the
        # current frame
        return [curves[key][knob].getValueAt(frame, i) for i in range(size)]

    for curve in curves.values():
        nuke.execute(curve, first, last, 1, views=[view])

    results = {}
    for frame in range(first, last + 1):
        average = at('counts', 'intensitydata', frame, 3)
        nan, inf = round(average[0] * pixels), round(average[1] * pixels)
        finite = pixels - nan - inf
        result: Dict[str, Any] = {'min': None, 'min_at': None, 'max': None, 'max_at': None,
                                  'mean': average[2] * pixels / finite if finite else None,
                                  'nan': nan, 'inf': inf}
        if 'over' in curves:
            result['over'] = round(at('over', 'intensitydata', frame, 1)[0] * pixels)
        if finite:
            result.update({
                'max': at('high', 'maxlumapixvalue', frame, 1)[0],
                'max_at': [int(v) for v in at('high', 'maxlumapixdata', frame, 2)],
                'min': at('low', 'minlumapixvalue', frame, 1)[0],
                'min_at': [int(v) for v in at('low', 'minlumapixdata', frame, 2)],
            })
        results[frame] = result
    return results


def _combine(per_frame: Dict[int, Dict[str, Any]], pixels: int) -> Dict[str, Any]:
    """Statistics of one channel over all measured frames."""
    results = per_frame.values()
    finite = {f: pixels - r['nan'] - r['inf'] for f, r in per_frame.items()}
    total = sum(finite.values())
    measured = {f: r for f, r in per_frame.items() if finite[f]}
    combined: Dict[str, Any] = {
        'min': None, 'min_at': None, 'min_frame': None,
        'max': None, 'max_at': None, 'max_frame': None,
        'mean': sum(r['mean'] * finite[f] for f, r in measured.items()) / total if total else None,
        'nan': sum(r['nan'] for r in results),
        'inf': sum(r['inf'] for r in results),
    }
    if measured:
        low = min(measured, key=lambda f: measured[f]['min'])
        high = max(measured, key=lambda f: measured[f]['max'])
        combined.update({'min': measured[low]['min'], 'min_at': measured[low]['min_at'],
                         'min_frame': low, 'max': measured[high]['max'],
                         'max_at': measured[high]['max_at'], 'max_frame': high})
    if 'over' in next(iter(results)):
        over = sum(r['over'] for r in results)
        worst = max(per_frame, key=lambda f: per_frame[f]['over'])
        combined.update({'over': over, 'over_fraction': over / (pixels * len(per_frame)),
                         'over_frame': worst if over else None})
    return combined


def stats(node: str = '', frame: Optional[int] = None, view: str = '', channels: str = 'rgb',
          crop: Optional[List[float]] = None, last: Optional[int] = None,
          over: Optional[float] = None) -> Dict[str, Any]:
    """Return exact statistics of `node` from `frame` to `last`, per channel."""
    viewer = nuke.activeViewer()
    source = _find_source(node, viewer)
    frame = nuke.frame() if frame is None else frame
    last = frame if last is None else last
    if last < frame:
        raise ToolError(f'last ({last}) is before frame ({frame}).')
    if over is not None and not isinstance(over, (int, float)):
        raise ToolError(f'over must be a number, got {over!r}.')
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

    warnings = _source_warnings(source, frame)
    if last != frame:
        warnings += [w for w in _source_warnings(source, last) if w not in warnings]

    start = time.monotonic()
    per_frame: Dict[str, Dict[int, Dict[str, Any]]] = {channel: {} for channel in picked}
    def measure(first, end):
        for channel in picked:
            try:
                per_frame[channel].update(_measure(curves[channel], pixels, first, end, view))
            except RuntimeError as e:
                raise ToolError(f'Cannot read {source.fullName()} at frames {first} to {end}: '
                                f'{e}') from None

    with temp_nodes('stats', source) as (name, image):
        curves = {channel: _channel_curves(image, channel, region, over, name)
                  for channel in picked}
        # the first frame alone tells how many frames fit in the time limit
        measure(frame, frame)
        if last > frame:
            spent = max(time.monotonic() - start, 0.001)
            end = min(last, frame + max(0, int((TIME_LIMIT - spent) / spent)))
            if end > frame:
                measure(frame + 1, end)
            if end < last:
                warnings.append(f'Frames {frame} to {last} would take about '
                                f'{spent * (last - frame + 1):.0f} s, over the {TIME_LIMIT:g} s '
                                f'limit: measured to frame {end}. Call again with '
                                f'frame={end + 1} for the rest.')
                last = end

    bad = sorted({f for frames in per_frame.values() for f, r in frames.items()
                  if r['nan'] or r['inf']})
    box = source.bbox()
    bbox = [box.x(), box.y(), box.x() + box.w(), box.y() + box.h()]
    if bbox[0] > region[0] or bbox[1] > region[1] or bbox[2] < region[2] or bbox[3] < region[3]:
        warnings.append(f'The bounding box {bbox} does not cover the region. Outside it, Nuke '
                        'repeats the edge pixels, and they are in these numbers.')

    return {
        'node': source.fullName(),
        'class': source.Class(),
        'frame': frame,
        'last': last,
        'view': view,
        'region': region,
        'pixels': pixels,
        'channels': {channel: _combine(frames, pixels) for channel, frames in per_frame.items()},
        'bad_frames': bad[:MAX_BAD_FRAMES],
        'seconds': round(time.monotonic() - start, 2),
        'warnings': warnings,
    }


STATS_TOOL = Tool(
    name='nuke_stats',
    description=(
        'Measure an image in Nuke: exact min, max and mean of each channel over one frame or '
        'a frame range of a node, with the pixel position and frame of the min and max, and '
        'the count of NaN and infinite pixels. It reads every pixel, so it finds a single hot '
        'or bad pixel. By default it measures the node feeding the active '
        'Viewer input, at the current frame, over the whole format. Use it to check clipping, '
        'black levels, NaN, or whether two images match; use nuke_vision to see the image.\n\n'
        '- Values are before the display transform, as stored in Nuke.\n'
        '- min, max and mean count only finite pixels. They are null when no pixel is '
        'finite.\n'
        '- Positions are [x, y] in Nuke pixels, y = 0 at the bottom.\n'
        '- crop: [x, y, width, height] in Nuke pixels.\n'
        '- last: measure every frame from frame to last. bad_frames lists the first 10 frames '
        f'with NaN or infinite pixels. After {TIME_LIMIT:g} s it stops, sets last to the last '
        'frame measured and warns; call again from the next frame.\n'
        '- over: also count the pixels at or above this value (over, over_fraction, and '
        'over_frame, the frame with the most). Use it to tell a few hot pixels from real '
        'clipping.\n'
        '- Nuke is busy while it computes. Temporary nodes do the work and are deleted; the '
        'scene and the undo history do not change.'
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
            'last': {'type': 'integer',
                     'description': 'Last frame of a range that starts at frame. Default: '
                                    'frame only.'},
            'over': {'type': 'number',
                     'description': 'Count the pixels at or above this value, for example 1.'},
        },
    },
    function=stats,
    timeout=TIMEOUT,
    annotations={'title': 'Measure an image in Nuke', 'readOnlyHint': True,
                 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False},
)

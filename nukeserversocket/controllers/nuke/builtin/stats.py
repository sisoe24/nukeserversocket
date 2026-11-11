"""Exact pixel statistics of one frame of a node: min, max, mean, NaN and infinity counts.

Built-in MCP tool nuke_stats. Code running in Nuke can call it too:

    from nukeserversocket.controllers.nuke.builtin.stats import stats
    print(stats('Grade1', frame=1001, channels='rgba'))

CurveTool reads every pixel, so a single hot pixel is found. Sampling a grid of points
misses it.
"""
from __future__ import annotations

import time
import inspect
from typing import Any

import nuke

from ._shared import (bbox, pick_view, temp_nodes, copy_to_rgb, find_source, pick_channels,
                      source_warnings)
from ....tools import Tool, ToolError

MAX_CHANNELS = 8
MAX_BAD_FRAMES = 10
NOT_FINITE = 'isnan(r)||isinf(r)'

# seconds; the bridge waits TIMEOUT for nuke_stats, whatever its --timeout
TIME_LIMIT = 40.0
TIMEOUT = 60.0

# 2**-64: scaling by a power of two keeps every value exact
SCALE = 2.0 ** -64

# the passes over each frame: (CurveTool operation, [red, green, blue] Expression)
PASSES = {
    # NaN in red, infinity in green, finite values (0 elsewhere) in blue
    'counts': ('Avg Intensities', ['isnan(r)?1:0', 'isinf(r)?1:0', f'{NOT_FINITE}?0:r']),
    # Max Luma Pixel finds a min only below 1 and a max only above 0, so both passes read the
    # min of values scaled below 1: high reads -r. It skips NaN but not infinity: push
    # non-finite values out.
    # shortcut: a value under 2e-19 loses precision; frames with all values over 1.8e19 fail
    'high': ('Max Luma Pixel', [f'{NOT_FINITE}?1e30:-r*{SCALE!r}'] * 3),
    'low': ('Max Luma Pixel', [f'{NOT_FINITE}?1e30:r*{SCALE!r}'] * 3),
}

PerFrame = dict[int, dict[str, Any]]


def _region(fmt: nuke.Format, crop: list[float] | None) -> list[int]:
    """Return the region to measure as [x, y, right, top]: the crop, or the whole format.

    Unlike nuke_vision, whole pixels only: the pixel count must be exact.
    """
    if crop is None:
        return [0, 0, fmt.width(), fmt.height()]

    if len(crop) != 4 or crop[2] < 1 or crop[3] < 1:
        raise ToolError('crop must be [x, y, width, height] with a width and height of '
                        'at least 1.')

    x, y, width, height = (round(value) for value in crop)
    return [x, y, x + width, y + height]


def _channel_curves(
    image: nuke.Node,
    channel: str,
    region: list[int],
    over: float | None,
    name: str,
) -> dict[str, nuke.Node]:
    """Make the CurveTools that measure one channel, in the current group."""
    # pipelines ignore nodes named _nss_*, so every node keeps the prefix
    prefix = f'{name}_{channel.replace(".", "_")}'
    shown = copy_to_rgb(image, [channel] * 3, f'{prefix}_copy')

    passes = dict(PASSES)
    if over is not None:
        passes['over'] = ('Avg Intensities', [f'r>={over!r}?1:0', '0', '0'])

    curves = {}
    for key, (operation, (red, green, blue)) in passes.items():
        expression = nuke.nodes.Expression(
            name=f'{prefix}_{key}',
            inputs=[shown],
            expr0=red,
            expr1=green,
            expr2=blue,
        )
        curve = nuke.nodes.CurveTool(
            name=f'{prefix}_{key}_curve',
            inputs=[expression],
            operation=operation,
        )
        curve['ROI'].setValue(region)
        curves[key] = curve
    return curves


def _measure(
    curves: dict[str, nuke.Node],
    pixels: int,
    first: int,
    last: int,
    view: str,
) -> PerFrame:
    """Statistics of one channel for each frame from first to last.

    Each pass runs once over the whole range: in the GUI, every execute opens the progress
    dialog and moves the timeline. Every frame costs the same, so the first frame tells how
    many fit in the time limit.
    """
    def at(key: str, knob: str, frame: int, size: int) -> list[float]:
        # a CurveTool run on several frames keys each one; in Nuke 17, value() reads the
        # current frame
        return [curves[key][knob].getValueAt(frame, i) for i in range(size)]

    for curve in curves.values():
        nuke.execute(curve, first, last, 1, views=[view])

    results = {}
    for frame in range(first, last + 1):
        average = at('counts', 'intensitydata', frame, 3)
        nan = round(average[0] * pixels)
        inf = round(average[1] * pixels)
        finite = pixels - nan - inf

        result: dict[str, Any] = {
            'min': None,
            'min_at': None,
            'max': None,
            'max_at': None,
            'mean': average[2] * pixels / finite if finite else None,
            'nan': nan,
            'inf': inf,
        }
        if 'over' in curves:
            result['over'] = round(at('over', 'intensitydata', frame, 1)[0] * pixels)
        if finite:
            result['max'] = -at('high', 'minlumapixvalue', frame, 1)[0] / SCALE
            result['max_at'] = [int(v) for v in at('high', 'minlumapixdata', frame, 2)]
            result['min'] = at('low', 'minlumapixvalue', frame, 1)[0] / SCALE
            result['min_at'] = [int(v) for v in at('low', 'minlumapixdata', frame, 2)]

        results[frame] = result
    return results


def _measure_channels(
    curves: dict[str, dict[str, nuke.Node]],
    pixels: int,
    first: int,
    last: int,
    view: str,
    source: nuke.Node,
) -> dict[str, PerFrame]:
    """Statistics of each channel for each frame from first to last."""
    measured = {}
    for channel, channel_curves in curves.items():
        try:
            measured[channel] = _measure(channel_curves, pixels, first, last, view)
        except RuntimeError as e:
            message = f'Cannot read {source.fullName()} at frames {first} to {last}: {e}'
            raise ToolError(message) from None
    return measured


def _combine(per_frame: PerFrame, pixels: int) -> dict[str, Any]:
    """Statistics of one channel over all measured frames."""
    results = per_frame.values()
    finite = {frame: pixels - r['nan'] - r['inf'] for frame, r in per_frame.items()}
    total = sum(finite.values())
    # frames with at least one finite pixel have a min and a max
    measured = {frame: r for frame, r in per_frame.items() if finite[frame]}

    mean = None
    if total:
        mean = sum(r['mean'] * finite[frame] for frame, r in measured.items()) / total

    combined: dict[str, Any] = {
        'min': None,
        'min_at': None,
        'min_frame': None,
        'max': None,
        'max_at': None,
        'max_frame': None,
        'mean': mean,
        'nan': sum(r['nan'] for r in results),
        'inf': sum(r['inf'] for r in results),
    }

    if measured:
        low = min(measured, key=lambda frame: measured[frame]['min'])
        high = max(measured, key=lambda frame: measured[frame]['max'])
        combined['min'] = measured[low]['min']
        combined['min_at'] = measured[low]['min_at']
        combined['min_frame'] = low
        combined['max'] = measured[high]['max']
        combined['max_at'] = measured[high]['max_at']
        combined['max_frame'] = high

    if 'over' in next(iter(results)):
        over = sum(r['over'] for r in results)
        worst = max(per_frame, key=lambda frame: per_frame[frame]['over'])
        combined['over'] = over
        combined['over_fraction'] = over / (pixels * len(per_frame))
        combined['over_frame'] = worst if over else None

    return combined


def stats(
    node: str = '',
    frame: int | None = None,
    view: str = '',
    channels: str = 'rgb',
    crop: list[float] | None = None,
    last: int | None = None,
    over: float | None = None,
) -> dict[str, Any]:
    """Return exact statistics of `node` from `frame` to `last`, per channel."""
    viewer = nuke.activeViewer()
    source = find_source(node, viewer)

    frame = nuke.frame() if frame is None else frame
    last = frame if last is None else last
    if last < frame:
        raise ToolError(f'last ({last}) is before frame ({frame}).')

    if over is not None and not isinstance(over, (int, float)):
        raise ToolError(f'over must be a number, got {over!r}.')

    if nuke.root()['proxy'].value():
        raise ToolError('Proxy mode is on: turn it off to measure the full-resolution image.')

    view = pick_view(view, viewer)

    picked = pick_channels(source, channels)
    if len(picked) > MAX_CHANNELS:
        raise ToolError(f'{channels!r} has {len(picked)} channels; at most {MAX_CHANNELS}.')

    region = _region(source.format(), crop)
    pixels = (region[2] - region[0]) * (region[3] - region[1])

    warnings = source_warnings(source, frame)
    if last != frame:
        warnings += [w for w in source_warnings(source, last) if w not in warnings]

    start = time.monotonic()
    with temp_nodes('stats', source) as (name, image):
        # with crop off, the bounding box becomes the region: CurveTool reads only inside
        # the bounding box
        image = nuke.nodes.Crop(name=f'{name}_fit', inputs=[image], crop=False)
        image['box'].setValue(region)
        curves = {
            channel: _channel_curves(image, channel, region, over, name) for channel in picked
        }
        per_frame = _measure_channels(curves, pixels, frame, frame, view, source)

        # the first frame alone tells how many frames fit in the time limit
        if last > frame:
            spent = max(time.monotonic() - start, 0.001)
            fits = max(0, int((TIME_LIMIT - spent) / spent))
            end = min(last, frame + fits)

            if end > frame:
                rest = _measure_channels(curves, pixels, frame + 1, end, view, source)
                for channel, frames in rest.items():
                    per_frame[channel].update(frames)

            if end < last:
                estimate = spent * (last - frame + 1)
                warnings.append(f'Frames {frame} to {last} would take about {estimate:.0f} s, '
                                f'over the {TIME_LIMIT:g} s limit: measured to frame {end}. '
                                f'Call again with frame={end + 1} for the rest.')
                last = end

    bad_frames = set()
    for frames in per_frame.values():
        bad_frames.update(f for f, result in frames.items() if result['nan'] or result['inf'])

    box = bbox(source)
    covered = (box[0] <= region[0] and box[1] <= region[1]
               and box[2] >= region[2] and box[3] >= region[3])
    if not covered:
        warnings.append(f'The bounding box {box} does not cover the region. The pixels '
                        'outside it count as 0.')

    return {
        'node': source.fullName(),
        'class': source.Class(),
        'frame': frame,
        'last': last,
        'view': view,
        'region': region,
        'pixels': pixels,
        'channels': {channel: _combine(frames, pixels) for channel, frames in per_frame.items()},
        'bad_frames': sorted(bad_frames)[:MAX_BAD_FRAMES],
        'seconds': round(time.monotonic() - start, 2),
        'warnings': warnings,
    }


DESCRIPTION = inspect.cleandoc(f"""
    Measure an image in Nuke: exact min, max and mean of each channel over one frame or a
    frame range of a node, with the pixel position and frame of the min and max, and the
    count of NaN and infinite pixels. It reads every pixel, so it finds a single hot or bad
    pixel. By default it measures the node feeding the active Viewer input, at the current
    frame, over the whole format. Use it to check clipping, black levels, NaN, or whether two
    images match; use nuke_vision to see the image.

    - Values are before the display transform, as stored in Nuke.
    - min, max and mean count only finite pixels. They are null when no pixel is finite.
    - Positions are [x, y] in Nuke pixels, y = 0 at the bottom.
    - crop: [x, y, width, height] in Nuke pixels.
    - last: measure every frame from frame to last. bad_frames lists the first
      {MAX_BAD_FRAMES} frames with NaN or infinite pixels. After {TIME_LIMIT:g} s it stops,
      sets last to the last frame measured and warns; call again from the next frame.
    - over: also count the pixels at or above this value (over, over_fraction, and
      over_frame, the frame with the most). Use it to tell a few hot pixels from real
      clipping.
    - It refuses to run in proxy mode.
    - Nuke is busy while it computes. Temporary nodes do the work and are deleted; the scene
      and the undo history do not change.
""")

STATS_TOOL = Tool(
    name='nuke_stats',
    description=DESCRIPTION,
    input_schema={
        'type': 'object',
        'properties': {
            'node': {
                'type': 'string',
                'description': 'Node to measure. Default: the node feeding the active Viewer '
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
                'description': 'Default "rgb". Or "rgba", "alpha", a layer such as "depth", '
                               f'or one channel. At most {MAX_CHANNELS} channels.',
            },
            'crop': {
                'type': 'array',
                'items': {'type': 'number'},
                'description': '[x, y, width, height] in Nuke pixels, y up.',
            },
            'last': {
                'type': 'integer',
                'description': 'Last frame of a range that starts at frame. Default: frame '
                               'only.',
            },
            'over': {
                'type': 'number',
                'description': 'Count the pixels at or above this value, for example 1.',
            },
        },
    },
    function=stats,
    timeout=TIMEOUT,
    annotations={
        'title': 'Measure an image in Nuke',
        'readOnlyHint': True,
        'destructiveHint': False,
        'idempotentHint': True,
        'openWorldHint': False,
    },
)

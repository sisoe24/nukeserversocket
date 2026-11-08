"""Phase 0 benchmarks for agent vision (docs/plans/agent-vision.md).

Run headless:  Nuke17.1 -ti bench.py <out_dir> [render|measure|edge|all]
Writes <out_dir>/<nuke version>_<suite>.json and the rendered images.
"""
from __future__ import annotations

import os
import sys
import json
import time
import uuid
import tempfile
from typing import Any, Callable

import nuke

SIZES = (512, 768, 1024, 1568)


# === FIXTURE === #

def build_light(seed: int = 0) -> nuke.Node:
    """HD comp: ramp background, checker card, text. About what a simple shot costs."""
    bg = nuke.nodes.Ramp(inputs=[nuke.nodes.Constant(format='HD_1080')], p0='0 0', p1='0 1080')
    card = nuke.nodes.CheckerBoard2(format='HD_1080', boxsize=64)
    card = nuke.nodes.Transform(inputs=[card], scale=0.4, translate=f'{seed % 7} 0')
    text = nuke.nodes.Text2(inputs=[bg], message='SMALL TEXT 12px', global_font_scale=0.2,
                            box='100 100 900 200')
    return nuke.nodes.Merge2(inputs=[text, card])


def build_heavy(seed: int = 0, fmt: str = 'UHD_4K') -> nuke.Node:
    """UHD comp with large blurs and defocus: seconds per frame when cold."""
    last = nuke.nodes.Noise(inputs=[nuke.nodes.Constant(format=fmt)], size=200, zoffset=seed * 0.37)
    for size in (80, 160, 240):
        blur = nuke.nodes.Blur(inputs=[last], size=size)
        last = nuke.nodes.Merge2(inputs=[last, blur], operation='screen')
    last = nuke.nodes.Defocus(inputs=[last], defocus=40)
    return nuke.nodes.Glow(inputs=[last], size=60)


def build_xheavy(seed: int = 0) -> nuke.Node:
    """build_heavy four times deeper: a slow shot."""
    last = build_heavy(seed)
    for _ in range(3):
        last = nuke.nodes.Defocus(inputs=[last], defocus=60)
        last = nuke.nodes.Glow(inputs=[last], size=120)
    return last


# === RENDER === #

def render(source: nuke.Node, frame: int, max_size: int | None, path: str,
           view: str | None = None, proxy: bool = False) -> dict[str, Any]:
    """Temporary Write to JPEG; return timings. The same path the spike tool used."""
    width, height = source.width(), source.height()
    scale = 1.0 if not max_size else min(1.0, max_size / max(width, height))
    nodes = []
    started = time.perf_counter()
    try:
        last = source
        if scale < 1:
            last = nuke.nodes.Reformat(type='scale', scale=scale, inputs=[source])
            nodes.append(last)
        write = nuke.nodes.Write(name=f'_bench_{uuid.uuid4().hex[:8]}', file=path,
                                 file_type='jpeg', channels='rgb', inputs=[last])
        nodes.append(write)
        write['colorspace'].setValue('sRGB')
        if proxy:
            write['proxy'].setValue(path)
        executed = time.perf_counter()
        nuke.execute(write, frame, frame, 1, views=[view or nuke.views()[0]])
        rendered = time.perf_counter()
    finally:
        for node in nodes:
            nuke.delete(node)
    return {
        'setup_s': round(executed - started, 4),
        'execute_s': round(rendered - executed, 4),
        'total_s': round(time.perf_counter() - started, 4),
        'width': round(width * scale), 'height': round(height * scale),
        'bytes': os.path.getsize(path),
    }


def suite_render(out_dir: str) -> list[dict[str, Any]]:
    results = []
    for name, build in (('light', build_light), ('heavy', build_heavy), ('xheavy', build_xheavy)):
        source = build(seed=1)
        for label in ('cold', 'warm'):
            path = os.path.join(out_dir, f'{name}_{label}.jpg')
            results.append({'script': name, 'cache': label, 'size': 1568,
                            **render(source, 1, 1568, path)})
        # a new seed changes the upstream hash: cold again without clearing the cache
        source = build(seed=2)
        for size in SIZES:
            path = os.path.join(out_dir, f'{name}_{size}.jpg')
            results.append({'script': name, 'cache': 'cold' if size == SIZES[0] else 'warm',
                            'size': size, **render(source, 1, size, path)})
        path = os.path.join(out_dir, f'{name}_full.jpg')
        results.append({'script': name, 'cache': 'warm', 'size': 'full',
                        **render(source, 1, None, path)})
    return results


# === MEASURE === #

def _timed(function: Callable[[], Any]) -> tuple[Any, float]:
    started = time.perf_counter()
    value = function()
    return value, round(time.perf_counter() - started, 4)


def _measures(width: int, height: int) -> dict[str, Callable[[nuke.Node], Any]]:
    box = (width // 4, height // 4, width // 2, height // 2)
    roi = f'{box[0]} {box[1]} {box[0] + box[2]} {box[1] + box[3]}'

    def points(count: int) -> Callable[[nuke.Node], Any]:
        coords = [((i * 97) % width + 0.5, (i * 53) % height + 0.5) for i in range(count)]
        return lambda node: [[node.sample(c, x, y, frame=1) for c in ('red', 'green', 'blue')]
                             for x, y in coords]

    def box_sample(node: nuke.Node) -> float:
        return node.sample('red', box[0] + box[2] / 2, box[1] + box[3] / 2, box[2], box[3], frame=1)

    def curvetool(node: nuke.Node) -> float:
        tool = nuke.nodes.CurveTool(inputs=[node], operation='Avg Intensities', ROI=roi)
        try:
            nuke.execute(tool, 1, 1)
            return tool['intensitydata'].valueAt(1, 0)
        finally:
            nuke.delete(tool)

    def grid(step: int) -> Callable[[nuke.Node], float]:
        def mean(node: nuke.Node) -> float:
            values = [node.sample('red', x + 0.5, y + 0.5, frame=1)
                      for y in range(box[1], box[1] + box[3], step)
                      for x in range(box[0], box[0] + box[2], step)]
            return sum(values) / len(values)
        return mean

    return {
        'sample 1 point (rgb)': points(1),
        'sample 10 points (rgb)': points(10),
        'sample 50 points (rgb)': points(50),
        'sample with dx/dy over region (red)': box_sample,
        'CurveTool Avg Intensities over region (red)': curvetool,
        'sample grid step 32 over region, mean (red)': grid(32),
        'sample grid step 8 over region, mean (red)': grid(8),
    }


def suite_measure(out_dir: str) -> list[dict[str, Any]]:
    results = []
    seed = 100
    for name, build in (('light', build_light), ('heavy', build_heavy), ('xheavy', build_xheavy)):
        probe = build(seed=0)
        for method, function in _measures(probe.width(), probe.height()).items():
            seed += 1
            # fresh seed per method: each starts cold
            source = build(seed=seed)
            value, cold = _timed(lambda: function(source))
            _, warm = _timed(lambda: function(source))
            if isinstance(value, list):
                value = value[0]
            results.append({'script': name, 'method': method, 'cold_s': cold, 'warm_s': warm,
                            'value': value})

        # does one render warm the cache for sample()?
        seed += 1
        source = build(seed=seed)
        rendered = render(source, 1, 768, os.path.join(out_dir, f'{name}_warmup.jpg'))
        sample_50 = _measures(source.width(), source.height())['sample 50 points (rgb)']
        _, after = _timed(lambda: sample_50(source))
        results.append({'script': name, 'method': 'render 768 then sample 50 points',
                        'render_s': rendered['total_s'], 'sample_s': after})
    return results


# === EDGE CASES === #

def _try(label: str, function: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return {'case': label, 'ok': True, **function()}
    except Exception as e:
        return {'case': label, 'ok': False, 'error': f'{type(e).__name__}: {e}'[:300]}


def suite_edge(out_dir: str) -> list[dict[str, Any]]:
    path = os.path.join(out_dir, 'edge.jpg')
    results = []

    group = nuke.nodes.Group(name='bench_group')
    with group:
        inner = nuke.nodes.CheckerBoard2(name='inner', format='HD_1080')
        nuke.nodes.Output(inputs=[inner])

    def in_group() -> dict[str, Any]:
        with group:
            return render(nuke.toNode('bench_group.inner'), 1, 768, path)

    results.append(_try('node inside group, Write created in the group', in_group))
    results.append(_try('node inside group, Write created in root',
                        lambda: render(nuke.toNode('bench_group.inner'), 1, 768, path)))

    nuke.root()['views'].fromScript('left #ff0000\nright #00ff00')
    stereo = nuke.nodes.Text2(inputs=[nuke.nodes.Constant(format='HD_1080')],
                              message='[view]', global_font_scale=2)
    results.append(_try('stereo, view right', lambda: render(stereo, 1, 768, path, 'right')))

    nuke.root()['proxy'].setValue(True)
    results.append(_try('proxy mode on', lambda: render(build_light(), 1, 768, path)))
    results.append(_try('proxy mode on, Write proxy knob set',
                        lambda: render(build_light(), 1, 768, path, proxy=True)))
    nuke.root()['proxy'].setValue(False)

    missing = nuke.nodes.Read(file='/nonexistent/plate.%04d.exr', first=1, last=10)
    results.append(_try('Read with a missing file', lambda: render(missing, 1, 768, path)))

    results.append(_try('Grade with no input', lambda: render(nuke.nodes.Grade(), 1, 768, path)))

    ranged = nuke.nodes.Read(file='/nonexistent/plate.%04d.exr', first=1, last=10,
                             on_error='black')
    results.append(_try('frame outside Read range (on_error black)',
                        lambda: render(ranged, 50, 768, path)))

    eight_k = nuke.nodes.Blur(inputs=[nuke.nodes.Noise(
        inputs=[nuke.nodes.Constant(format='8K_LatLong')])], size=50)
    results.append(_try(f'large format {eight_k.width()}x{eight_k.height()}',
                        lambda: render(eight_k, 1, 1568, path)))
    return results


SUITES = {'render': suite_render, 'measure': suite_measure, 'edge': suite_edge}


def main() -> None:
    out_dir = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix='nss_bench_')
    names = sys.argv[2:] or ['all']
    names = list(SUITES) if names == ['all'] else names
    version = nuke.NUKE_VERSION_STRING
    for name in names:
        suite_dir = os.path.join(out_dir, f'{version}_{name}')
        os.makedirs(suite_dir, exist_ok=True)
        results = SUITES[name](suite_dir)
        with open(os.path.join(out_dir, f'{version}_{name}.json'), 'w') as f:
            json.dump(results, f, indent=1, default=str)
        print(f'BENCH {version} {name}')
        for row in results:
            print(json.dumps(row, default=str))


if __name__ == '__main__':
    main()

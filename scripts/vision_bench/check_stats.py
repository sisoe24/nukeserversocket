"""Exercise nuke_stats headless: Nuke -ti check_stats.py. Fails on the first wrong result."""
from __future__ import annotations

import os
import sys
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import nuke

from nukeserversocket.tools import ToolError
from nukeserversocket.controllers.nuke.builtin.stats import stats


def raises(**kwargs):
    try:
        stats(**kwargs)
    except ToolError as e:
        return str(e)
    raise AssertionError(f'no ToolError for {kwargs}')


def close(a, b):
    return abs(a - b) < 1e-6


nuke.addFormat('64 64 1 nss64')
base = nuke.nodes.Constant(name='Base', format='nss64')
base['color'].setValue([0.5, 0.5, 0.5, 1])
# red: NaN at (10, 10), +inf at (20, 20), 7 at (40, 40); green: -2 at (30, 30)
bad = nuke.nodes.Expression(
    name='Bad', inputs=[base],
    expr0='(x==10&&y==10)?sqrt(-1):(x==20&&y==20)?1/0:(x==40&&y==40)?7:0.5',
    expr1='(x==30&&y==30)?-2:0.5', expr2='0.5')
depth = nuke.nodes.Copy(name='Depth', inputs=[bad, bad])
depth['from0'].setValue('rgba.green')
depth['to0'].setValue('depth.Z')
lonely = nuke.nodes.Grade(name='Lonely')
small = nuke.nodes.Crop(name='Small', inputs=[base])
small['box'].setValue([0, 0, 32, 32])
no_alpha = nuke.nodes.Remove(name='NoAlpha', inputs=[base], operation='remove',
                             channels='alpha')
assert 'rgba.alpha' not in no_alpha.channels(), no_alpha.channels()
nodes_before = len(nuke.allNodes(recurseGroups=True))
undo_before = nuke.Undo.disabled()
nuke.root().setModified(False)

reply = stats(node='Bad', frame=1)
print(json.dumps(reply))
red, green, blue = (reply['channels'][c] for c in ('rgba.red', 'rgba.green', 'rgba.blue'))
assert reply['pixels'] == 64 * 64 and reply['region'] == [0, 0, 64, 64]
assert (red['nan'], red['inf']) == (1, 1), red
assert red['max'] == 7 and red['max_at'] == [40, 40], red
assert red['min'] == 0.5, red
assert close(red['mean'], (4093 * 0.5 + 7) / 4094), red
assert (green['nan'], green['inf']) == (0, 0) and green['min'] == -2 and green['min_at'] == [30, 30]
assert close(green['mean'], (4095 * 0.5 - 2) / 4096), green
assert blue['min'] == blue['max'] == 0.5 and close(blue['mean'], 0.5)
assert reply['warnings'] == [], reply['warnings']
assert not nuke.root().modified()

alpha = stats(node='Bad', frame=1, channels='alpha')['channels']
assert list(alpha) == ['rgba.alpha'] and alpha['rgba.alpha']['max'] == 1
assert list(stats(node='Bad', frame=1, channels='rgba')['channels']) == [
    'rgba.red', 'rgba.green', 'rgba.blue', 'rgba.alpha']
layer = stats(node='Depth', frame=1, channels='depth')['channels']
assert list(layer) == ['depth.Z'] and layer['depth.Z']['min'] == -2, layer
assert list(stats(node='Depth', frame=1, channels='depth.Z')['channels']) == ['depth.Z']

cropped = stats(node='Bad', frame=1, crop=[35, 35, 10, 10])
assert cropped['region'] == [35, 35, 45, 45] and cropped['pixels'] == 100
assert cropped['channels']['rgba.red']['max_at'] == [40, 40]
assert cropped['channels']['rgba.red']['nan'] == 0

assert 'does not cover' in stats(node='Small', frame=1)['warnings'][-1]

assert 'No node named' in raises(node='Nope')
assert 'no channel or layer' in raises(node='Bad', channels='nope')
assert 'has no rgba.alpha' in raises(node='NoAlpha', channels='rgba')
assert 'no image' in raises(node='Lonely')
assert 'crop must be' in raises(node='Bad', crop=[0, 0, 0, 5])
assert 'No view' in raises(node='Bad', view='left')

assert len(nuke.allNodes(recurseGroups=True)) == nodes_before
assert not [n for n in nuke.allNodes(recurseGroups=True) if n.name().startswith('_nss')]
assert nuke.Undo.disabled() == undo_before

# the hot pixel that a grid of samples misses, on a 2K frame
black = nuke.nodes.Constant(name='Black')
hot = nuke.nodes.Expression(name='Hot', inputs=[black], expr0='(x==100&&y==100)?50:0',
                            expr1='0', expr2='0')
start = time.time()
hot_red = stats(node='Hot', frame=1)['channels']['rgba.red']
print(f'2K rgb: {time.time() - start:.3f} s')
assert hot_red['max'] == 50 and hot_red['max_at'] == [100, 100], hot_red

print('OK', nuke.NUKE_VERSION_STRING)

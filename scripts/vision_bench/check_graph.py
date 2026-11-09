"""Exercise nuke_graph headless: Nuke -ti check_graph.py. Fails on the first wrong result."""
from __future__ import annotations

import os
import sys
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import nuke

from nukeserversocket.tools import ToolError
from nukeserversocket.controllers.nuke.builtin.graph import graph


def by_name(reply):
    return {n['name']: n for n in reply['nodes']}


def raises(**kwargs):
    try:
        graph(**kwargs)
    except ToolError as e:
        return str(e)
    raise AssertionError(f'no ToolError for {kwargs}')


bg = nuke.nodes.CheckerBoard2(name='Checker')
blur = nuke.nodes.Blur(name='Blur1', inputs=[bg], size=4)
merge = nuke.nodes.Merge2(name='Merge1', inputs=[blur, None])
merge.setInput(2, bg)
read = nuke.nodes.Read(name='Missing', file='/nonexistent/plate.%04d.exr', first=1, last=10)
off = nuke.nodes.Grade(name='Off', inputs=[blur], disable=True, label='artist note')
long_text = nuke.nodes.Text2(name='Long', message='x' * 5000)
grp = nuke.nodes.Group(name='Grp')
with grp:
    nuke.nodes.Blur(name='Inner', inputs=[nuke.nodes.Input()])
    nuke.nodes.Output(inputs=[nuke.toNode('Inner')])
nuke.root().setModified(False)

reply = graph()
# reads only
assert not nuke.root().modified()
nodes = by_name(reply)
print(json.dumps(reply)[:600])
print('reply characters', len(json.dumps(reply)))

assert reply['group'] == 'root'
assert set(nodes) == {'Checker', 'Blur1', 'Merge1', 'Missing', 'Off', 'Long', 'Grp'}, nodes
assert nodes['Blur1']['inputs'] == ['Checker'] and nodes['Blur1']['knobs'] == {'size': '4'}
assert nodes['Merge1']['inputs'] == ['Blur1', None, 'Checker'], nodes['Merge1']['inputs']
assert nodes['Missing'].get('error') is True
assert nodes['Off']['knobs']['disable'] == 'true', nodes['Off']['knobs']
assert nodes['Off']['knobs']['label'] == 'artist note', nodes['Off']['knobs']
assert 'error' not in nodes['Blur1']
assert nodes['Long']['knobs']['message'].startswith('<cut: '), nodes['Long']['knobs']
assert nodes['Grp']['children'] == 3
assert not {'xpos', 'ypos', 'name', 'selected'} & set(nodes['Blur1']['knobs'])
# selecting a node is not a change
blur.setSelected(True)
unchanged = graph(since=reply['snapshot'])['nodes']
assert unchanged == [], unchanged
assert graph()['selected'] == ['Blur1']
blur.setSelected(False)
assert reply['script']['views'] == nuke.views() and reply['viewer'] is None
assert 'truncated' not in reply and 'removed' not in reply

inner = graph(group='Grp')
assert inner['group'] == 'Grp' and set(by_name(inner)) == {'Grp.Input1', 'Grp.Inner', 'Grp.Output1'}
assert by_name(inner)['Grp.Inner']['inputs'] == ['Grp.Input1']

capped = graph(max_nodes=2)
assert len(capped['nodes']) == 2 and capped['truncated'].startswith('2 of 7')

# since: knob change, new input, move, new node, deleted node
snap = graph()['snapshot']
assert graph(since=snap)['nodes'] == []
blur['size'].setValue(9)
off.setInput(0, bg)
long_text.setXYpos(500, 500)
nuke.nodes.Dot(name='NewDot')
nuke.delete(read)
diff = graph(since=snap)
assert set(by_name(diff)) == {'Blur1', 'Off', 'Long', 'NewDot'}, set(by_name(diff))
assert diff['removed'] == ['Missing'], diff['removed']

unknown = graph(since='nope')
assert unknown['warnings'] and len(unknown['nodes']) == 7
other_group = graph(group='Grp', since=diff['snapshot'])
assert other_group['warnings'] and len(other_group['nodes']) == 3

# only the last 4 snapshots are kept
old = graph()['snapshot']
for _ in range(4):
    graph()
assert graph(since=old)['warnings']

assert 'No node named' in raises(group='Nope')
assert 'not a Group' in raises(group='Blur1')
assert 'max_nodes' in raises(max_nodes=0)

# UI state is left out: hidden knobs, toolbar settings, Viewer knobs
paint = nuke.nodes.RotoPaint(name='Paint')
viewer = nuke.nodes.Viewer(name='View', inputs=[blur])
ui = by_name(graph())
assert 'old_message' not in ui['Long']['knobs'] and 'message' in ui['Long']['knobs']
assert not [k for k in ui['Long']['knobs'] if 'toolbar' in k], ui['Long']['knobs']
assert 'toolbox' not in ui['Paint']['knobs'] and 'curves' in ui['Paint']['knobs']
assert ui['View']['knobs'] == {} and ui['View']['inputs'] == ['Blur1']

with nuke.nodes.Group(name='Big'):
    for i in range(200):
        nuke.nodes.Grade(name=f'G{i}', white=1 + i / 100)
start = time.time()
big = graph(group='Big')
print(f'200 nodes: {time.time() - start:.4f} s, {len(json.dumps(big))} characters')

print('OK', nuke.NUKE_VERSION_STRING)

"""Exercise nuke_vision headless: Nuke -ti check_vision.py <out_dir>."""
from __future__ import annotations

import os
import sys
import glob
import tempfile
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import nuke

from nukeserversocket.tools import ToolError
from nukeserversocket.controllers.nuke_vision import vision, _set_display

OUT = sys.argv[1]


def case(label, **kwargs):
    print(f'CASE {label} {kwargs}')
    try:
        image = vision(**kwargs)
    except ToolError as e:
        print(f'  TOOLERROR {e}')
        return
    except Exception:
        print('  EXCEPTION ' + traceback.format_exc().replace('\n', ' | '))
        return
    path = os.path.join(OUT, f'{nuke.NUKE_VERSION_STRING}_{label}.jpg')
    with open(path, 'wb') as f:
        f.write(image.data)
    print(f'  IMAGE {len(image.data)} bytes -> {path}')


nodes_before = len(nuke.allNodes(recurseGroups=True))

bg = nuke.nodes.CheckerBoard2(name='Checker', format='HD_1080')
text = nuke.nodes.Text2(name='Label', inputs=[bg], message='VISION 1040')
text['font_size'].setValue(200)
text['box'].setValue([100, 100, 1800, 500])
text['color'].setValue([1, 0.2, 0.2, 1])
depth = nuke.nodes.Copy(name='WithDepth', inputs=[text, nuke.nodes.Ramp(inputs=[bg])])
depth['from0'].setValue('rgba.red')
depth['to0'].setValue('depth.Z')
nuke.addFormat('1024 512 2.0 nss_anamorphic')
anam = nuke.nodes.CheckerBoard2(name='Anamorphic', format='nss_anamorphic')
read = nuke.nodes.Read(name='Plate', file='/nonexistent/plate.%04d.exr', first=1, last=10,
                       on_error='black')
grade = nuke.nodes.Grade(name='Lonely')
nodes_fixture = len(nuke.allNodes(recurseGroups=True))

case('no_viewer')
case('missing', node='NoSuchNode')
case('rgb', node='Label', frame=1)
case('alpha', node='Label', channels='alpha')
case('depth_layer', node='WithDepth', channels='depth')
case('bad_layer', node='WithDepth', channels='nope')
case('crop', node='Label', crop=[100, 100, 400, 200])
case('bad_crop', node='Label', crop=[0, 0, 10])
case('anamorphic', node='Anamorphic')
case('outside_range', node='Plate', frame=50)
case('empty_input', node='Lonely')
case('bad_size', node='Label', size=10)
nuke.root()['proxy'].setValue(True)
case('proxy', node='Label')
nuke.root()['proxy'].setValue(False)

print('LEFTOVER nodes', nodes_fixture, len(nuke.allNodes(recurseGroups=True)),
      [n.name() for n in nuke.allNodes(recurseGroups=True) if n.name().startswith('_nss')])
print('LEFTOVER files', glob.glob(os.path.join(tempfile.gettempdir(), 'nss_vision_*')))
print('UNDO disabled', nuke.Undo.disabled())

# display transform parsing against an OCIO config
root = nuke.root()
root['colorManagement'].setValue('OCIO')
configs = root['OCIO_config'].values()
aces = next((c for c in configs if 'aces' in c.lower() or 'cg-config' in c.lower()), None)
print('OCIO configs', configs)
if aces:
    root['OCIO_config'].setValue(aces)
    w = nuke.nodes.Write()
    displays, views = w['display'].values(), w['view'].values()
    print('DISPLAY', aces, displays[:3], views[:3])
    if displays and views:
        print('SET', _set_display(w, f'{views[0]} ({displays[0]})'), '|', w['transformType'].value())
    print('SET none', _set_display(nuke.nodes.Write(), None))
    print('SET bogus', _set_display(nuke.nodes.Write(), 'Not A View (Nope)'))

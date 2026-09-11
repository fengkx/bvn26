import sys
from pathlib import Path

ROOT = Path('/Users/fengkx/me/code/bvn2_6')
sys.path.insert(0, str(ROOT / 'tools/probes'))
import build_ai_reference as b

original = b.instrument

def instrument(source, origin, fighter):
    updated = original(source, origin, fighter)
    if origin == 'fighter/fz/you#frame_48/PlaceObject2_24_3/CLIPACTIONRECORD onClipEvent(enterFrame).as':
        needle = '   if(this.hitTest(_root.game["p" + _parent.pn].mc.bdmn))'
        hook = '''   var _geomTarget = _root.game["p" + _parent.pn].mc.bdmn;
   var _geomOwn = this.getBounds(_root);
   var _geomTargetBounds = _geomTarget.getBounds(_root);
   var _geomParent = _parent.transform.concatenatedMatrix;
   _root.aiEvent("you_geometry", String(this) + "," + _currentframe + "," + String(_geomTarget) + "," + typeof(_geomTarget) + "," + _root.game["p" + _parent.pn].mc._currentframe + "," + _geomTarget._currentframe + "," + _geomOwn.xMin + "," + _geomOwn.yMin + "," + _geomOwn.xMax + "," + _geomOwn.yMax + "," + _geomTargetBounds.xMin + "," + _geomTargetBounds.yMin + "," + _geomTargetBounds.xMax + "," + _geomTargetBounds.yMax + "," + _geomParent.a + "," + _geomParent.b + "," + _geomParent.c + "," + _geomParent.d + "," + _geomParent.tx + "," + _geomParent.ty + "," + this.hitTest(_geomTarget));
''' + needle
        if updated.count(needle) != 1:
            raise RuntimeError('missing unique You frame 48 hitTest')
        updated = updated.replace(needle, hook)
    return updated

b.instrument = instrument
import argparse
p = argparse.ArgumentParser()
p.add_argument('--ffdec', required=True, type=Path)
p.add_argument('--output', required=True, type=Path)
p.add_argument('--run-id', required=True)
p.add_argument('--move-case', required=True, type=Path)
a = p.parse_args()
result = b.build(a.ffdec.resolve(), a.output.resolve(), a.run_id, 300,
                 p1_character='佐助', p2_character='恋次',
                 move_case=a.move_case.resolve(), dynamic_move_case=True,
                 p1_helper='you', p2_helper='kon')
print(result)

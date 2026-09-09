"""Capture mode-specific transitions while keeping the original selector code."""
import json,subprocess
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Build an analysis-only original selection probe')
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--ffdec', type=Path, required=True)
args=parser.parse_args()
out=args.output
if out.exists(): raise ValueError('Use a new probe directory')
patch=out/'patch'
patch.mkdir(parents=True)
b=json.load(open('scripts/main.json'))['scripts']
def write(path,source):
 p=patch/'scripts'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
for s in b:
 if s['path'] in [f'DefineSprite_{i}/frame_1/DoAction.as' for i in (1477,1480,1505)]:
  write(s['path'],s['source'].replace('Key.isDown(', '_root.selectionKey('))
 if s['path'].startswith('frame_56/') and '/DoAction' in '/'+s['path']:write(s['path'],'stop();')
write('frame_10/DoAction.as','''stop();
if (_root.selectionMode == undefined) _root.selectionMode = 1;
_root.modo = _root.selectionMode;
_root.stage = 1;
_root.selectionKey = function(code) {
 return _root.selectionTick % 35 == 20 && (code == _root.j || (_root.modo == 3 && code == _root.N1));
};
_root.selectionNext = function() {
 delete _root.onEnterFrame;
 _root.selectionMode++;
 if (_root.selectionMode > 4) { trace("SELECTION_REF|DONE"); fscommand("quit"); }
 else _root.gotoAndStop(10);
};
_root.gotoAndStop("选人画面");
''')
write('frame_46/DoAction.as','''stop();
_root.selectionTick = 0;
_root.onEnterFrame = function() {
 _root.selectionTick++;
 var m = _root.xure.xrmc;
 trace("SELECTION_REF|"+_root.modo+"|"+_root.selectionTick+"|"+_root.xure._currentframe+"|"+m.isFZ+"|"+m.isMap+"|"+m.p1enable+"|"+m.p2enable+"|"+_root.p1selt+"|"+_root.p2selt+"|"+_root.p1sf+"|"+_root.p2sf+"|"+m.curx1+"|"+m.cury1+"|"+m.curx2+"|"+m.cury2);
 if (m.isMap && _root.selectionTick % 35 == 10) _root.selectionNext();
 if (_root.selectionTick > 280) { trace("SELECTION_REF|TIMEOUT"); _root.selectionNext(); }
};
''')
write('frame_56/DoAction.as','''stop();
trace("SELECTION_REF|BATTLE|"+_root.modo+"|"+_root.p1selt+"|"+_root.p2selt+"|"+_root.p1sf+"|"+_root.p2sf);
_root.selectionNext();
''')
subprocess.run(['java','-Djava.awt.headless=true','-jar',str(args.ffdec),'-importScript','game/main.swf',str(out/'selection.swf'),str(patch)],check=True,stdout=subprocess.DEVNULL)

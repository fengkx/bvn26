"""Measure native AS2 MovieClip coordinate storage in a windowed minimal SWF."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from build_minimal_swf import build

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--ffdec',type=Path,required=True)
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'game').mkdir()
    patch=args.output/'patch/frame_1';patch.mkdir(parents=True)
    original=args.output/'minimal.swf';original.write_bytes(build(1))
    code=(HERE/'as2/ai_reference/number.as').read_text()+'''
Stage.displayState = "normal";
Stage.scaleMode = "showAll";
stop();
var seq = 0;
var obj = _root.createEmptyMovieClip("measured", 1);
function emit(kind, value) {
   trace("AIREF|coordinate-r1|" + (++seq) + "|" + getTimer() + "|0|0|" + kind + "|" + value);
}
var values = [0,0.024,0.025,0.049,0.05,0.051,-0.024,-0.025,-0.049,-0.05,-0.051,14.4,-14.4,314.4,-314.4];
for(var i = 0; i < values.length; i++) {
   obj._x = values[i]; obj._y = values[i];
   emit("set", aiNumber(values[i]) + "," + aiNumber(obj._x) + "," + aiNumber(obj._y));
}
for(var sign = -1; sign <= 1; sign += 2) {
   obj._x = 300 * sign; obj._y = -25;
   for(var step = 0; step < 20; step++) {
      obj._x += 14.4 * sign; obj._y -= 19.2;
      emit("step", sign + "," + step + "," + aiNumber(obj._x) + "," + aiNumber(obj._y));
   }
}
emit("done", "");
fscommand("quit");
'''
    (patch/'DoAction.as').write_text(code)
    target=args.output/'game/main.swf'
    run=subprocess.run(['java','-Djava.awt.headless=true','-jar',str(args.ffdec),'-importScript',str(original),str(target),str(args.output/'patch')],capture_output=True,text=True,check=True)
    (args.output/'build.log').write_text(run.stdout+run.stderr)
    (args.output/'build.json').write_text(json.dumps({'run_id':'coordinate-r1','scope':'native AS2 coordinate setter; synthetic clip, not combat acceptance','player_display':'windowed_showAll','script_sha256':hashlib.sha256(code.encode()).hexdigest(),'swf_sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2)+'\n')


if __name__=='__main__':main()

"""Build an isolated native getBounds/BitmapData rounding probe."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from build_minimal_swf import rect, tag

ROOT = Path(__file__).resolve().parents[2]


def build(ffdec: Path, output: Path, run_id: str):
    output.mkdir(parents=True, exist_ok=False)
    (output / 'game').mkdir()
    body = rect(0, 12000, 0, 8000) + struct.pack('<HH', 30 * 256, 1) + tag(12, b'\0') + tag(1) + tag(0)
    base = output / 'base.swf'
    base.write_bytes(b'FWS\x08' + struct.pack('<I', len(body) + 8) + body)
    script = output / 'patch/frame_1/DoAction.as'
    script.parent.mkdir(parents=True)
    source = '''Stage.displayState="normal";
var seq=0;
function emit(kind,value) { trace("AIREF|__ID__|"+(seq++)+"|"+getTimer()+"|0|0|"+kind+"|"+value); }
createEmptyMovieClip("actor",1);
actor.createEmptyMovieClip("inner",1);
var p=actor.inner;
p.beginFill(0x336699,100);p.moveTo(-12.35,-7.15);p.lineTo(12.35,-7.15);p.lineTo(12.35,7.15);p.lineTo(-12.35,7.15);p.endFill();
var scales=[100.07019,99.9,33.33333,150.1,-100.07019];
for(var i=0;i<scales.length;i++) {
 p._xscale=scales[i];p._yscale=scales[i];
 var b=actor.getBounds(actor);
 emit("bounds",p._xscale+","+p._yscale+","+b.xMin+","+b.yMin+","+b.xMax+","+b.yMax+","+actor._width+","+actor._height);
}
p.clear();p._xscale=100;p._yscale=100.07019;p._y=-23.9;
p.createEmptyMovieClip("nested",1);
p.nested._y=-45.15;
p.nested.beginFill(0x336699,100);p.nested.moveTo(0,19.5);p.nested.lineTo(45,19.5);p.nested.lineTo(45,92.5);p.nested.lineTo(0,92.5);p.nested.endFill();
var b=actor.getBounds(actor);emit("nested_bounds",b.xMin+","+b.yMin+","+b.xMax+","+b.yMax);
emit("done",true);stop();fscommand("quit");
'''.replace('__ID__', run_id)
    script.write_text(source)
    movie = output / 'game/main.swf'
    with (output / 'build.log').open('w') as log:
        subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec), '-importScript', str(base), str(movie), str(output / 'patch')], check=True, stdout=log, stderr=subprocess.STDOUT)
    report = {'run_id': run_id, 'source': source, 'swf_sha256': hashlib.sha256(movie.read_bytes()).hexdigest(), 'scope': 'synthetic FP32 numeric probe; original game input is unchanged'}
    (output / 'build.json').write_text(json.dumps(report, indent=2)+'\n')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args()
    build(args.ffdec,args.output,args.run_id)

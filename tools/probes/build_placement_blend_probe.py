"""Measure difference/overlay object compositing in native Flash, without a tolerance."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import uuid

from build_minimal_swf import rect, tag


def cases():
    return [{'mode': mode, 'back': back, 'front': front, 'back_alpha': ba,
             'front_alpha': fa, 'opacity': opacity}
            for mode in [7, 13]
            for back, front in [(0x3366cc, 0xcc80aa), (0x007fff, 0xff8000), (0x80ff01, 0x407ffe)]
            for ba, fa, opacity in [(255, 255, 100), (153, 178, 100), (255, 128, 100),
                                    (0, 255, 100), (255, 255, 50)]]


def build(output, ffdec):
    output.mkdir(parents=True, exist_ok=False)
    run_id = 'placement-blend-' + uuid.uuid4().hex[:12]
    code = '''stop();var seq=0;
function emit(k,v){trace("AIREF|placement-blend-r17|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function square(parent,name,depth,color,alpha){var m=parent.createEmptyMovieClip(name,depth);m.beginFill(color,alpha*100/255);m.moveTo(0,0);m.lineTo(8,0);m.lineTo(8,8);m.lineTo(0,8);m.endFill();return m;}
'''
    for i, c in enumerate(cases()):
        code += f'''var w=createEmptyMovieClip("w",1);square(w,"back",1,{c['back']},{c['back_alpha']});
var g=w.createEmptyMovieClip("g",2);g.blendMode="{'difference' if c['mode']==7 else 'overlay'}";g._alpha={c['opacity']};square(g,"front",1,{c['front']},{c['front_alpha']});
var pix=new flash.display.BitmapData(8,8,true,0);pix.draw(w.back);emit("back","{i},"+pix.getPixel32(4,4));pix.fillRect(pix.rectangle,0);pix.draw(g.front);emit("front","{i},"+pix.getPixel32(4,4));pix.fillRect(pix.rectangle,0);pix.draw(w);emit("pixel","{i},"+pix.getPixel32(4,4));var black=new flash.display.BitmapData(8,8,false,0);black.draw(pix);emit("black","{i},"+black.getPixel32(4,4));black.dispose();pix.dispose();w.removeMovieClip();
'''
    code += 'emit("done","ok");fscommand("quit");'
    code = code.replace('placement-blend-r17', run_id)
    scripts = output / 'scripts/frame_1'
    scripts.mkdir(parents=True)
    (scripts/'DoAction.as').write_text(code)
    body = rect(0, 320, 0, 320) + struct.pack('<HH', 30*256, 1) + tag(12, b'\0') + tag(1) + tag(0)
    base = output / 'base.swf'
    base.write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
    movie = output / 'game/main.swf'
    movie.parent.mkdir()
    subprocess.run(['java',f'-Duser.home={output.resolve()}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(base),str(movie),str(output/'scripts')],check=True)
    (output/'build.json').write_text(json.dumps({'run_id':run_id,'outputs_sha256':{'game/main.swf':hashlib.sha256(movie.read_bytes()).hexdigest()},'probe_source_sha256':hashlib.sha256(code.encode()).hexdigest(),'cases':cases()},indent=2)+'\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    args = parser.parse_args()
    build(args.output, args.ffdec)

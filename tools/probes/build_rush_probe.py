#!/usr/bin/env python3
"""Capture the locked XG_rush definition without rewriting its timeline/actions."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib
import uuid

from build_minimal_swf import rect, tag

ROOT = Path(__file__).resolve().parents[2]


def source_definitions(path: Path) -> bytes:
    raw = path.read_bytes()
    body = raw[8:] if raw[:3] == b'FWS' else zlib.decompress(raw[8:])
    offset = (5 + 4 * (body[0] >> 3) + 7) // 8 + 4
    result = []
    while offset < len(body):
        start = offset
        header = struct.unpack_from('<H', body, offset)[0]
        offset += 2
        code, size = header >> 6, header & 63
        if size == 63:
            size = struct.unpack_from('<I', body, offset)[0]
            offset += 4
        offset += size
        if code not in (0, 1, 9, 12, 26, 28, 43, 56, 59, 69, 70, 76, 82, 86):
            result.append(body[start:offset])
    return b''.join(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = ROOT / 'game/main.swf'
    effect = json.loads((ROOT / 'godot/generated/effects/XG_rush/effect.json').read_text())
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == effect['source_swf']['sha256']
    exports = tag(56, struct.pack('<HH', 1, effect['sprite_id']) + b'XG_rush\0')
    body = rect(0, 5120, 0, 5120) + struct.pack('<HH', 30 * 256, 1)
    body += source_definitions(source) + exports + tag(12, b'\0') + tag(1) + tag(0)
    base = args.output / 'base.swf'
    base.write_bytes(b'FWS' + bytes([8]) + struct.pack('<I', len(body) + 8) + body)
    code = '''stop();var seq=0;var tick=0;
function emit(k,v){trace("AIREF|rush-r05|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
var holder=createEmptyMovieClip("holder",1);var mc=holder.attachMovie("XG_rush","fx",1);mc._x=128;mc._y=128;
function observe(){
 var alive=mc._totalframes>1;emit("clock",alive?mc._currentframe:0);
 var b=new flash.display.BitmapData(256,256,false,0);b.draw(holder);
 var row="";for(var y=64;y<=192;y+=16){for(var x=64;x<=192;x+=16){row+=b.getPixel(x,y)+",";}}emit("pixels",row);b.dispose();
}
observe();onEnterFrame=function(){tick++;observe();if(tick>=20){delete onEnterFrame;emit("done","ok");fscommand("quit");}};
'''
    run_id = 'rush-r05-' + uuid.uuid4().hex[:8]
    code = code.replace('rush-r05', run_id)
    scripts = args.output / 'scripts/frame_1';scripts.mkdir(parents=True)
    (scripts / 'DoAction.as').write_text(code)
    output = args.output / 'game/main.swf';output.parent.mkdir()
    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec), '-importScript',
                    str(base), str(output), str(args.output / 'scripts')], check=True)
    if source_definitions(output) != source_definitions(source):
        raise ValueError('Probe import changed original SWF definition tags')
    (args.output / 'build.json').write_text(json.dumps({'run_id': run_id, 'source': 'game/main.swf',
        'source_sha256': digest, 'ffdec_sha256': hashlib.sha256(args.ffdec.read_bytes()).hexdigest(),
        'definitions_sha256': hashlib.sha256(source_definitions(source)).hexdigest(), 'probe_source_sha256': hashlib.sha256(code.encode()).hexdigest(),
        'outputs_sha256': {'game/main.swf': hashlib.sha256(output.read_bytes()).hexdigest()},
        'method': 'Raw original definition tags; attach XG_rush at 128,128; no source action edits.'}, indent=2)+'\n')

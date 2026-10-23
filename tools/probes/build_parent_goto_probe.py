#!/usr/bin/env python3
"""Observe real parent/body replacement without changing child frame actions."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import struct
import zlib
import uuid

from build_rush_probe import source_definitions

ROOT = Path(__file__).resolve().parents[2]


def non_action_tags(path: Path) -> bytes:
    raw = path.read_bytes()
    body = raw[8:] if raw[:3] == b'FWS' else zlib.decompress(raw[8:])
    offset = (5 + 4 * (body[0] >> 3) + 7) // 8 + 4
    records = []
    while offset < len(body):
        start = offset
        header = struct.unpack_from('<H', body, offset)[0]
        offset += 2
        kind, size = header >> 6, header & 63
        if size == 63:
            size = struct.unpack_from('<I', body, offset)[0]
            offset += 4
        offset += size
        if kind != 12:
            records.append(body[start:offset])
    return b''.join(records)


def build(fighter: str, ffdec: Path, output: Path) -> None:
    timeline = json.loads((ROOT / f'godot/generated/fighters/{fighter}/timeline.json').read_text())
    source = ROOT / timeline['source_swf']['path']
    bundle = json.loads((ROOT / str(source.relative_to(ROOT)).replace('game/', 'scripts/', 1).replace('.swf', '.json')).read_text())
    scripts = {s['path']: s['source'] for s in bundle['scripts']}
    prefix = f"DefineSprite_{timeline['sprite_id']}/frame_"
    sites = [(p, s) for p, s in scripts.items() if p.startswith(prefix) and s.strip() == '_parent.gotoAndStop(2);']
    if len(sites) != 1:
        raise ValueError(f'Expected one exact parent goto: {sites}')
    frame = int(sites[0][0].split('/')[1][6:])
    run_id = 'parent-goto-' + fighter + '-' + uuid.uuid4().hex[:8]
    code = '_root.zhanting=true;\n' + scripts['frame_1/DoAction.as'] + '''
var __seq=0;var __tick=0;var __old;
zhanting=true;
function __emit(k,v){trace("AIREF|RUN_ID|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
function __observe(tag){__emit("state",tag+","+_currentframe+","+mc._currentframe+","+(mc===__old)+","+mc.__sentinel+","+mc.spd+","+mc.jumpPower+","+mc.khit+","+mc.touch);}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){
  __old=mc;mc.__sentinel=73;mc.khit=91;__observe("before");
  mc.gotoAndPlay(SOURCE_FRAME);__observe("after_call");
 }else{__observe("next_tick");}
 if(__tick>=4){delete onEnterFrame;__emit("done","ok");fscommand("quit");}
};
'''
    code = code.replace('RUN_ID', run_id).replace('SOURCE_FRAME', str(frame))
    output.mkdir(parents=True, exist_ok=False)
    patch = output / 'scripts/frame_1/DoAction.as'
    patch.parent.mkdir(parents=True)
    patch.write_text(code)
    movie = output / 'game/main.swf'
    movie.parent.mkdir()
    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec), '-importScript',
                    str(source), str(movie), str(output / 'scripts')], check=True)
    original = source_definitions(source)
    if source_definitions(movie) != original:
        raise ValueError('Native probe changed original definition tags')
    if non_action_tags(movie) != non_action_tags(source):
        raise ValueError('Native probe changed original non-action root tags')
    metadata = {'non_action_tags_sha256': hashlib.sha256(non_action_tags(source)).hexdigest(), 'run_id': run_id, 'source': str(source.relative_to(ROOT)),
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'source_call_path': sites[0][0], 'source_call': sites[0][1],
                'definitions_sha256': hashlib.sha256(original).hexdigest(),
                'ffdec_sha256': hashlib.sha256(ffdec.read_bytes()).hexdigest(),
                'probe_source_sha256': hashlib.sha256(code.encode()).hexdigest(),
                'outputs_sha256': {'game/main.swf': hashlib.sha256(movie.read_bytes()).hexdigest()},
                'scope': 'Original root placements and child actions; root observer forces source goto frame with movement paused.'}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fighter', required=True, choices=['daitu', 'minren', 'sasuke', 'yihu'])
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    build(args.fighter, args.ffdec, args.output)

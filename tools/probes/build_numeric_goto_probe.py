#!/usr/bin/env python3
"""Capture numeric goto playback using the unmodified Rukia body definition."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import uuid

from build_minimal_swf import rect, tag
from build_rush_probe import source_definitions

ROOT = Path(__file__).resolve().parents[2]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = ROOT / 'game/fighter/rukia.swf'
    effect = json.loads((ROOT / 'godot/generated/fighters/rukia/timeline.json').read_text())
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == effect['source_swf']['sha256']
    exports = tag(56, struct.pack('<HH', 1, effect['sprite_id']) + b'body\0')
    body = rect(0, 5120, 0, 5120) + struct.pack('<HH', 30 * 256, 1)
    body += source_definitions(source) + exports + tag(12, b'\0') + tag(1) + tag(0)
    base = args.output / 'base.swf'
    base.write_bytes(b'FWS' + bytes([8]) + struct.pack('<I', len(body) + 8) + body)
    code = '''stop();var seq=0;var tick=0;
function emit(k,v){trace("AIREF|numeric-goto-r06|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
var holder=createEmptyMovieClip("holder",1);var mc=holder.attachMovie("body","mc",1);
zhanting=true;mc.touch=false;mc.speed=0;
mc.gotoAndPlay(130);
emit("clock",mc._currentframe);
onEnterFrame=function(){tick++;emit("clock",mc._currentframe);if(tick>=30){delete onEnterFrame;emit("done","ok");fscommand("quit");}};
'''
    run_id = 'numeric-goto-r06-' + uuid.uuid4().hex[:8]
    code = code.replace('numeric-goto-r06', run_id)
    scripts = args.output / 'scripts/frame_1';scripts.mkdir(parents=True)
    (scripts / 'DoAction.as').write_text(code)
    output = args.output / 'game/main.swf';output.parent.mkdir()
    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec), '-importScript',
                    str(base), str(output), str(args.output / 'scripts')], check=True)
    if source_definitions(output) != source_definitions(source):
        raise ValueError('Probe import changed original SWF definition tags')
    (args.output / 'build.json').write_text(json.dumps({'run_id': run_id, 'source': 'game/fighter/rukia.swf',
        'source_sha256': digest, 'ffdec_sha256': hashlib.sha256(args.ffdec.read_bytes()).hexdigest(),
        'definitions_sha256': hashlib.sha256(source_definitions(source)).hexdigest(), 'probe_source_sha256': hashlib.sha256(code.encode()).hexdigest(),
        'outputs_sha256': {'game/main.swf': hashlib.sha256(output.read_bytes()).hexdigest()},
        'method': 'Raw original Rukia definitions; attach body 533, gotoAndPlay(130), pause movement callbacks; retain original frame 141 gotoAndPlay(130). No source action edits.'}, indent=2)+'\n')

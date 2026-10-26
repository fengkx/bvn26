"""Observe original single-frame special aliases across blank frame actions."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

from build_parent_goto_probe import ROOT, non_action_tags, source_definitions


def build(fighter, parent_frame, sprite, start_frame, ffdec, output):
    source = ROOT / f'game/fighter/{fighter}.swf'
    bundle = json.loads((ROOT / f'scripts/fighter/{fighter}.json').read_text())
    scripts = {item['path']: item['source'] for item in bundle['scripts']}
    run_id = 'special-cost-' + fighter + '-' + uuid.uuid4().hex[:8]
    code = '_root.zhanting=true;\n' + scripts['frame_1/DoAction.as'] + '''
var __seq=0;var __tick=0;
function __emit(k,v){trace("AIREF|RUN_ID|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){gotoAndStop(PARENT_FRAME);}
 else if(__tick==2){mc.ql=234;mc.gotoAndPlay(START_FRAME);__emit("start",mc._currentframe+","+mc.ql);}
 else if(__tick<=5){__emit("advance",mc._currentframe+","+mc.ql);}
 else{delete onEnterFrame;__emit("done","ok");fscommand("quit");}
};
'''
    code = code.replace('RUN_ID', run_id).replace('PARENT_FRAME', str(parent_frame)).replace('START_FRAME', str(start_frame))
    output.mkdir(parents=True, exist_ok=False)
    patch = output / 'scripts/frame_1/DoAction.as'
    patch.parent.mkdir(parents=True)
    patch.write_text(code)
    movie = output / 'game/main.swf'
    movie.parent.mkdir()
    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec), '-importScript', str(source), str(movie), str(output / 'scripts')], check=True)
    assert source_definitions(movie) == source_definitions(source)
    assert non_action_tags(movie) == non_action_tags(source)
    digest = lambda data: hashlib.sha256(data).hexdigest()
    metadata = {'run_id': run_id, 'source': str(source.relative_to(ROOT)), 'source_sha256': digest(source.read_bytes()),
                'sprite_id': sprite, 'parent_frame': parent_frame, 'start_frame': start_frame,
                'definitions_sha256': digest(source_definitions(source)), 'non_action_tags_sha256': digest(non_action_tags(source)),
                'ffdec_sha256': digest(ffdec.read_bytes()), 'probe_source_sha256': digest(code.encode()),
                'outputs_sha256': {'game/main.swf': digest(movie.read_bytes())},
                'scope': 'Only root frame 1 observer changed; original definitions and placement tags unchanged. Paused movement, forced source label frame, original frame actions execute.'}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fighter', required=True)
    parser.add_argument('--parent-frame', type=int, required=True)
    parser.add_argument('--sprite', type=int, required=True)
    parser.add_argument('--start-frame', type=int, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.fighter, args.parent_frame, args.sprite, args.start_frame, args.ffdec, args.output)

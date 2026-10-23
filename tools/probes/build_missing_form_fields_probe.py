#!/usr/bin/env python3
"""Observe missing target-body fields using unchanged original child actions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

from build_parent_goto_probe import non_action_tags
from build_rush_probe import source_definitions

ROOT = Path(__file__).resolve().parents[2]
CASES = {'sasuke': ('Sasuke', 1019, 'khitn', 128, 135),
         'yihu': ('yihu', 1180, 'nn', 143, 143)}


def build(fighter: str, ffdec: Path, output: Path, controller_branch: bool = False) -> dict:
    name, sprite, field, action_frame, child_frame = CASES[fighter]
    source = ROOT / f'game/fighter/{name}.swf'
    bundle_path = ROOT / f'scripts/fighter/{name}.json'
    bundle = json.loads(bundle_path.read_text())
    scripts = {script['path']: script['source'] for script in bundle['scripts']}
    occurrences = [{'path': path, 'source': text,
                    'source_sha256': hashlib.sha256(text.encode()).hexdigest()}
                   for path, text in scripts.items() if re.search(r'\b' + field + r'\b', text)]
    run_id = 'missing-form-fields-' + fighter + '-' + uuid.uuid4().hex[:8]
    root = '_root.zhanting=true;\n' + scripts['frame_1/DoAction.as']
    code = root + '''
var __seq=0;var __tick=0;
function __emit(k,v){trace("AIREF|RUN_ID|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
function __observe(tag){__emit("field",tag+","+_currentframe+","+mc._currentframe+","+mc.FIELD+","+typeof(mc.FIELD)+","+mc.hasOwnProperty("FIELD")+","+isNaN(mc.FIELD)+","+(mc.FIELD<3)+","+(mc.FIELD>=1));}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){gotoAndStop(2);}
 if(__tick==2){__observe("initial");mc.gotoAndStop(ACTION_FRAME);__observe("after_call");}
 if(__tick==3){__observe("action_executed");mc.gotoAndStop(CHILD_FRAME);}
 if(__tick==4){__observe("child_frame");SEED_ACTION}
 if(__tick==5){__observe("seeded_result");delete mc.FIELD;__observe("deleted");mc.gotoAndStop(ACTION_FRAME);}
 if(__tick==6){__observe("reentered_result");delete onEnterFrame;__emit("done","ok");fscommand("quit");}
};
'''
    if controller_branch:
        code = root + """
var __seq=0;var __tick=0;
function __emit(k,v){trace("AIREF|RUN_ID|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
function __observe(tag){__emit("branch",tag+","+_currentframe+","+mc._currentframe+","+mc.FIELD+","+typeof(mc.FIELD)+","+mc.touch+","+_y);}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){gotoAndStop(2);}
 if(__tick==2){mc.on_enterframe=function(){};mc.gotoAndStop(ACTION_FRAME);}
 if(__tick==3){mc.gotoAndStop(CHILD_FRAME);mc.touch=true;_y=0;__observe("before_callback");zhanting=false;}
 if(__tick==4){__observe("after_callback");zhanting=true;delete onEnterFrame;__emit("done","ok");fscommand("quit");}
};
"""
        if fighter == 'sasuke':
            code = code.replace('mc.touch=true;_y=0;', 'mc.touch=true;_y=0;useAI=false;mc.pn=1;game={p1:{mc:{sw:false}}};mc.斩=17;mc.招=18;mc.kis=function(key){return key==17;};')
            code = code.replace('if(__tick==4){__observe("after_callback");zhanting=true;', 'if(__tick==4){__observe("after_callback");mc.khitn=0;__observe("seeded");}\n if(__tick==5){__observe("seeded_callback");zhanting=true;')
        else:
            code = code.replace('if(__tick==4){__observe("after_callback");zhanting=true;', 'if(__tick==4){__observe("after_callback");mc.nn=0;mc.gotoAndStop(143);mc.touch=true;_y=0;__observe("seeded_zero");}\n if(__tick==5){__observe("zero_callback");zhanting=true;')
    seed_action = f'mc.{field}=0;__observe("seeded");mc.gotoAndStop({action_frame});' if fighter == 'sasuke' else f'mc.{field}=1;__observe("seeded");'
    for key, value in {'RUN_ID': run_id, 'FIELD': field, 'ACTION_FRAME': str(action_frame),
                       'CHILD_FRAME': str(child_frame), 'SEED_ACTION': seed_action}.items():
        code = code.replace(key, value)
    output = output.resolve()
    if output == ROOT or any(output == ROOT / p or ROOT / p in output.parents for p in ('game', 'scripts')):
        raise ValueError('Probe output must not overwrite locked source')
    patch = output / 'scripts/frame_1/DoAction.as'
    patch.parent.mkdir(parents=True)
    patch.write_text(code)
    movie = output / 'game/main.swf'
    movie.parent.mkdir()
    subprocess.run(['java', f'-Duser.home={output}', '-Djava.awt.headless=true', '-jar', str(ffdec),
                    '-importScript', str(source), str(movie), str(output / 'scripts')], check=True)
    definitions = source_definitions(source)
    if source_definitions(movie) != definitions or non_action_tags(movie) != non_action_tags(source):
        raise ValueError('Probe changed original definition or non-action root tags')
    report = {'run_id': run_id, 'source': str(source.relative_to(ROOT)),
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'bundle': str(bundle_path.relative_to(ROOT)),
              'bundle_sha256': hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
              'target_body_sprite': sprite, 'field': field, 'all_bundle_field_occurrences': occurrences,
              'definitions_sha256': hashlib.sha256(definitions).hexdigest(),
              'non_action_tags_sha256': hashlib.sha256(non_action_tags(source)).hexdigest(),
              'ffdec_sha256': hashlib.sha256(ffdec.read_bytes()).hexdigest(),
              'probe_source_sha256': hashlib.sha256(code.encode()).hexdigest(),
              'outputs_sha256': {'game/main.swf': hashlib.sha256(movie.read_bytes()).hexdigest()},
              'controller_branch': controller_branch,
              'scope': 'Root observer forces parent frame2 and target action; original child definitions/actions unchanged. ' +
                       ('Original child callback dispatch active with touch=true and body on_enterframe replaced by no-op to isolate it.' if controller_branch else 'Movement paused; controller callback branch dispatch is not tested. Seeded and deleted states are explicit diagnostics.')}
    (output / 'build.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fighter', choices=CASES, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--controller-branch', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.fighter, args.ffdec, args.output, args.controller_branch), ensure_ascii=False, indent=2))

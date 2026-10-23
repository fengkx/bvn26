"""Observe Minren transfers and initial placement-filter retirement in native Flash."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

from build_parent_goto_probe import ROOT, source_definitions, non_action_tags

OBSERVER = """
var __seq=0;var __tick=0;var __third=false;
maxhp=1500;game={p1:this,p2:this};p1bs="original";p2bs="original";
function __emit(k,v){trace("AIREF|minren-graph-r14|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
function __obs(tag){__emit("state",tag+","+_currentframe+","+mc._currentframe+","+mc.hp+","+mc.ql+","+mc.filters.length+","+中转.hp+","+中转.ql);}
onEnterFrame=function(){
 __tick++;__obs("before");
 if(__tick==1){mc.hp=671;mc.ql=234;mc.pn=2;mc.gotoAndPlay(1379);__obs("after_start");}
 if(_currentframe==2 && mc._currentframe>1 && !__third){clearInterval(feiint);clearInterval(feiint2);mc.gotoAndPlay(1157);__third=true;__obs("after_third_goto");}
 if(_currentframe==3 && mc._currentframe>1){__obs("third_initialized");delete onEnterFrame;__emit("done","ok");fscommand("quit");}
 if(__tick>12){delete onEnterFrame;__emit("done","timeout");fscommand("quit");}
};
"""


def build(output: Path, ffdec: Path, slot: int) -> None:
    source = ROOT / 'game/fighter/minren.swf'
    bundle = json.loads((ROOT / 'scripts/fighter/minren.json').read_text())
    scripts = {item['path']: item['source'] for item in bundle['scripts']}
    run_id = 'minren-graph-' + uuid.uuid4().hex[:8]
    observer = OBSERVER.replace('minren-graph-r14', run_id).replace('mc.pn=2;', f'mc.pn={3-slot};')
    code = '_root.zhanting=true;\n' + scripts['frame_1/DoAction.as'] + observer
    output.mkdir(parents=True, exist_ok=False)
    patch = output / 'scripts/frame_1/DoAction.as'
    patch.parent.mkdir(parents=True)
    patch.write_text(code)
    movie = output / 'game/main.swf'
    movie.parent.mkdir()
    subprocess.run(['java', f'-Duser.home={output.resolve()}', '-Djava.awt.headless=true',
                    '-jar', str(ffdec), '-importScript', str(source), str(movie),
                    str(output / 'scripts')], check=True)
    assert source_definitions(source) == source_definitions(movie)
    assert non_action_tags(source) == non_action_tags(movie)
    report = {'run_id': run_id, 'source': str(source.relative_to(ROOT)), 'slot': slot,
              'probe_source_sha256': hashlib.sha256(code.encode()).hexdigest(),
              'ffdec_sha256': hashlib.sha256(ffdec.read_bytes()).hexdigest(),
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'outputs_sha256': {'game/main.swf': hashlib.sha256(movie.read_bytes()).hexdigest()},
              'scope': 'Root observer only; source child definitions and non-action root tags unchanged. '
                       'Explicit pn and HP/energy seed; both game slot paths alias the root wrapper. '
                       'Intervals cleared before forcing the second parent transition.'}
    (output / 'build.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--slot', type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    build(args.output, args.ffdec, args.slot)

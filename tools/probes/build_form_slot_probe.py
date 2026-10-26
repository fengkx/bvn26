"""Observe the authored Sasuke slot transfer sequence and captured health callback."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

from build_parent_goto_probe import ROOT, non_action_tags, source_definitions


def build(ffdec: Path, output: Path, slot: int):
    source = ROOT / 'game/fighter/Sasuke.swf'
    scripts = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/fighter/Sasuke.json').read_text())['scripts']}
    run_id = 'form-slot-' + uuid.uuid4().hex[:8]
    code = '_root.zhanting=true;\n' + scripts['frame_1/DoAction.as'] + '''
var __seq=0;var __tick=0;var __fn;var __old;
maxhp=1500;p1bs="p1-original";p2bs="p2-original";
game={p1:this,p2:this};
上箭=101;下箭=102;左箭=103;右箭=104;N1=105;N2=106;N3=107;N4=108;N5=109;N6=110;
function __emit(k,v){trace("AIREF|RUN_ID|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
function __observe(){__emit("state",_currentframe+","+mc._currentframe+","+p1bs+","+p2bs+","+中转.hp+","+中转.ql+","+mc.hp+","+mc.ql+","+万解);}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){mc.hp=671;mc.ql=234;mc.pn=PN;mc.wudi=true;__old=mc;mc.gotoAndPlay(1228);}
 __observe();
 if(mc._currentframe==1230){__fn=mc.feixue;clearInterval(feiint);clearInterval(feiint2);__emit("timer",typeof feiint+","+typeof feiint2);}
 if(_currentframe==2 && __tick>=6){
  __emit("live",__old===mc);
  mc.wudi=true;zhanting=false;__fn();__emit("damage",mc.hp);
  mc.hp=300;__fn();__emit("floor",mc.hp);
  mc.hp=301;__fn();__emit("cross_floor",mc.hp);
  zhanting=true;__fn();__emit("paused",mc.hp);
  delete onEnterFrame;__emit("done","ok");fscommand("quit");
 }
 if(__tick>12){delete onEnterFrame;__emit("done","timeout");fscommand("quit");}
};
'''
    code = code.replace('RUN_ID', run_id).replace('PN', str(2 if slot == 1 else 1))
    output.mkdir(parents=True, exist_ok=False)
    patch = output / 'scripts/frame_1/DoAction.as'
    patch.parent.mkdir(parents=True)
    patch.write_text(code)
    movie = output / 'game/main.swf'
    movie.parent.mkdir()
    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec), '-importScript', str(source), str(movie), str(output / 'scripts')], check=True)
    assert source_definitions(movie) == source_definitions(source)
    assert non_action_tags(movie) == non_action_tags(source)
    metadata = {'run_id': run_id, 'source': str(source.relative_to(ROOT)),
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'source_sites': ['DefineSprite_603/frame_%d/DoAction.as' % f for f in [1228, 1229, 1230, 1232]],
                'ffdec_sha256': hashlib.sha256(ffdec.read_bytes()).hexdigest(),
                'outputs_sha256': {'game/main.swf': hashlib.sha256(movie.read_bytes()).hexdigest()},
                'slot': slot, 'probe_source_sha256': hashlib.sha256(code.encode()).hexdigest(),
                'definitions_sha256': hashlib.sha256(source_definitions(source)).hexdigest(),
                'non_action_tags_sha256': hashlib.sha256(non_action_tags(source)).hexdigest(),
                'scope': 'Root observer only; child actions unchanged. game.p1/p2 alias the root wrapper; pn is explicitly seeded. Captured source callback delivered manually after clearing its real interval to isolate semantics.'}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--slot', type=int, choices=[1, 2], required=True)
    args = parser.parse_args()
    build(args.ffdec, args.output, args.slot)

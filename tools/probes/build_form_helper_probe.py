"""Observe original wankai/doWanKai transfer without replacing their code."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

from build_parent_goto_probe import ROOT, non_action_tags, source_definitions


def build(fighter, ffdec, output, observe_frames=False, observe_stage=False):
    timeline = json.loads((ROOT / f'godot/generated/fighters/{fighter}/timeline.json').read_text())
    source = ROOT / timeline['source_swf']['path']
    bundle = json.loads((ROOT / str(source.relative_to(ROOT)).replace('game/', 'scripts/', 1).replace('.swf', '.json')).read_text())
    scripts = {s['path']: s['source'] for s in bundle['scripts']}
    run_id = 'form-helper-' + fighter + '-' + uuid.uuid4().hex[:8]
    code = '_root.zhanting=true;\n' + scripts['frame_1/DoAction.as'] + '''
var __seq=0;var __tick=0;
上箭=101;下箭=102;左箭=103;右箭=104;N1=105;N2=106;N3=107;N4=108;N5=109;N6=110;
function __emit(k,v){trace("AIREF|RUN_ID|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
function __observe(tag){
 __emit(tag,万解+","+中转.hp+","+中转.ql+","+_y+","+mc.hp+","+mc.ql);
}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){
  mc.hp=671;mc.ql=234;mc.wudi=true;_y=17;
  mc.wankai();__observe("after_call");
 }else if(__tick==2){
  __observe("after_replace");
  __emit("keys",mc.上+","+mc.下+","+mc.左+","+mc.右+","+mc.斩+","+mc.跳+","+mc.冲+","+mc.招+","+mc.必杀+","+mc.换);
  __emit("interval",typeof feiint);
  delete onEnterFrame;__emit("done","ok");fscommand("quit");
 }
};
'''
    if observe_stage:
        if fighter != 'yihu':
            raise ValueError('Stage observation currently has a Yihu native input fixture')
        code = code.replace('}else if(__tick==2){', '}else if(__tick>=2){')
        code = code.replace('delete onEnterFrame;__emit("done","ok");fscommand("quit");',
                            'if(__tick==24){delete onEnterFrame;__emit("done","ok");fscommand("quit");}')
        observe_frames = True
    if observe_frames:
        code = code.replace('__observe("after_replace");', '__observe("after_replace");__emit("frames",_currentframe+","+mc._currentframe);')
    code = code.replace('RUN_ID', run_id)
    output.mkdir(parents=True, exist_ok=False)
    patch = output / 'scripts/frame_1/DoAction.as'
    patch.parent.mkdir(parents=True)
    patch.write_text(code)
    movie = output / 'game/main.swf'
    movie.parent.mkdir()
    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec), '-importScript',
                    str(source), str(movie), str(output / 'scripts')], check=True)
    assert source_definitions(movie) == source_definitions(source), 'Changed definition tags'
    assert non_action_tags(movie) == non_action_tags(source), 'Changed root placement tags'
    metadata = {'run_id': run_id, 'source': str(source.relative_to(ROOT)),
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'source_call_path': f'DefineSprite_{timeline["sprite_id"]}/frame_1/DoAction.as#wankai',
                'definitions_sha256': hashlib.sha256(source_definitions(source)).hexdigest(),
                'non_action_tags_sha256': hashlib.sha256(non_action_tags(source)).hexdigest(),
                'ffdec_sha256': hashlib.sha256(ffdec.read_bytes()).hexdigest(),
                'probe_source_sha256': hashlib.sha256(code.encode()).hexdigest(),
                'outputs_sha256': {'game/main.swf': hashlib.sha256(movie.read_bytes()).hexdigest()},
                'probe_kind': 'form_helper_nested_stage' if observe_stage else ('form_helper_transfer_frames' if observe_frames else 'form_helper_transfer'),
                'scope': 'Original wankai/doWanKai and nested definitions/placements unchanged; root observer invokes original helper with useAI undefined, wudi=true and paused movement. Not full combat/form replay.'}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observe-stage', action='store_true')
    parser.add_argument('--observe-frames', action='store_true')
    parser.add_argument('--fighter', required=True, choices=['daitu', 'minren', 'sasuke', 'yihu', 'byakuya', 'rifagu', 'rukia'])
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.fighter, args.ffdec, args.output, args.observe_frames, args.observe_stage)

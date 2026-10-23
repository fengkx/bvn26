"""Observe original Yihu third-form flip callback and replacement helper."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

from build_parent_goto_probe import ROOT, non_action_tags, source_definitions


def build(case, ffdec, output):
    fighter = "yihu"
    parent_frame, sprite, start_frame = (3, 1672, 390) if case == "flip" else (2, 1180, 1)
    source = ROOT / f'game/fighter/{fighter}.swf'
    bundle = json.loads((ROOT / f'scripts/fighter/{fighter}.json').read_text())
    scripts = {item['path']: item['source'] for item in bundle['scripts']}
    run_id = 'yihu-third-form-' + fighter + '-' + uuid.uuid4().hex[:8]
    code = '_root.zhanting=true;\n' + scripts['frame_1/DoAction.as'] + '''
var __seq=0;var __tick=0;
function __emit(k,v){trace("AIREF|RUN_ID|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){gotoAndStop(PARENT_FRAME);}
 else if(__tick==2){
  mc.on_enterframe=function(){};mc.gotoAndStop(390);mc.pn=1;
  game={p1:{mc:{bdmn:{},jiao:{}}}};mc.zh10atm={hitTest:function(){return true;}};
  _xscale=75;__emit("before",mc._currentframe+","+_xscale);zhanting=false;
 }else if(__tick==3){
  zhanting=true;__emit("after",mc._currentframe+","+_xscale);
  delete onEnterFrame;__emit("done","ok");fscommand("quit");
 }
};
'''
    if case == 'helper':
        code = '_root.zhanting=true;\n' + scripts['frame_1/DoAction.as'] + '\n' + """
var __seq=0;var __tick=0;
上箭=101;下箭=102;左箭=103;右箭=104;N1=105;N2=106;N3=107;N4=108;N5=109;N6=110;
function __emit(k,v){trace("AIREF|RUN_ID|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
function __observe(k){__emit(k,_currentframe+","+mc._currentframe+","+万解+","+中转.hp+","+中转.ql+","+_y+","+mc.hp+","+mc.ql);}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){gotoAndStop(2);}
 else if(__tick==2){mc.hp=671;mc.ql=234;mc.wudi=true;_y=17;mc.wankai();__observe("after_call");}
 else if(__tick==3){
  __observe("after_replace");
  __emit("keys",mc.上+","+mc.下+","+mc.左+","+mc.右+","+mc.斩+","+mc.跳+","+mc.冲+","+mc.招+","+mc.必杀+","+mc.换);
  delete onEnterFrame;__emit("done","ok");fscommand("quit");
 }
};
"""
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
                'case': case, 'sprite_id': sprite, 'parent_frame': parent_frame, 'start_frame': start_frame,
                'definitions_sha256': digest(source_definitions(source)), 'non_action_tags_sha256': digest(non_action_tags(source)),
                'ffdec_sha256': digest(ffdec.read_bytes()), 'probe_source_sha256': digest(code.encode()),
                'outputs_sha256': {'game/main.swf': digest(movie.read_bytes())},
                'scope': 'Only root frame 1 observer changed; original definitions and placement tags unchanged. Helper: paused original body helper, explicit transfer input. Flip: original child callback with body enterFrame no-op and true hitTest stub, xscale75. Not full combat parity.'}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['flip', 'helper'], required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.case, args.ffdec, args.output)

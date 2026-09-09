"""Check compiled callbacks against source with a measured removal adapter.

This verifies ordered dispatch translation. Body effects and geometry remain
explicit test doubles; target frame scripts are queued, not evaluated here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/importer'))
from compile_ai_controller import compile_controller
from compile_ai_predicates import compile_source
from check_ai_predicates import fixtures

NODE=r'''
const fs=require('fs'),vm=require('vm');
const dir=process.argv[2], input=JSON.parse(fs.readFileSync(dir+'/input.json','utf8'));
const outputs=input.cases.map(test=>{
 const s=structuredClone(test.state), events=[], removed={}; let alive=true;
 const defined=v=>v===null?undefined:v;
 const fields={_x:'x',_y:'y',_xscale:'xscale',scale_X:'scale_X'};
 const container=new Proxy({useAI:true,_curGJL:s.power,moveX:v=>events.push(['move_axis','moveX',v]),moveY:v=>events.push(['move_axis','moveY',v])},{
  get(o,k){return k in fields?defined(s[fields[k]]):o[k]},
  set(o,k,v){if(k in fields){s[fields[k]]=v;events.push(['write',fields[k],v])}else o[k]=v;return true}
 });
 function jump(label,play){
  if(!(label in input.labels))throw new Error('Unverified missing label '+label);
  events.push(['goto',label,play]);
  alive=test.hook.member_frames.includes(input.labels[label]);
  if(!alive)throw removed;
 }
 const body=new Proxy({pn:2,_parent:container,AImain:{},gotoAndPlay:l=>jump(l,true),gotoAndStop:l=>jump(l,false),
  resColor:()=>events.push(['effect','resColor']),updateDirect:()=>events.push(['effect','updateDirect']),
  fangyux:(...a)=>events.push(['body_call','fangyux',a]),beidax:(...a)=>events.push(['body_call','beidax',a])},{
  get(o,k){return k in s?defined(s[k]):o[k]},
  set(o,k,v){if(k in s){s[k]=v;events.push(['write',k,v])}else o[k]=v;return true}
 });
 for(const key of Object.keys(s.sensors))body.AImain[key]={hitTest:()=>s.sensors[key]};
 body.zh20atm={hitTest:()=>s.body_hits.zh20atm};
 const context={_parent:body,touchFloor:defined(s.controller_touchFloor),_root:{zhanting:defined(s.root_paused),zhongli:s.gravity,
  jumpxg:()=>events.push(['effect','jumpxg']),luodixg:()=>events.push(['effect','luodixg']),game:{
  p2:{_x:s.opponent_x,_y:s.opponent_y,mc:{动作:s.opponent_action,sw:defined(s.opponent_sw),bdmn:{}}},
  p2fz:{动作:s.opponent_helper_action}}},isNaN};
 vm.createContext(context);vm.runInContext(input.source,context);
 for(let i=0;i<3&&alive;i++){
  try{vm.runInContext(input.callbacks[test.hook.method],context)}catch(e){if(e!==removed)throw e}
 }
 return {events,alive,locals:[context.js,context.jumpinggg??null,context.standed,context.allF,context.walkF]};
});
fs.writeFileSync(dir+'/expected.json',JSON.stringify(outputs));
'''
ADAPTER='''extends RefCounted
var state: Dictionary
var labels: Dictionary
var members: Array
var alive := true
var events: Array = []
func _init(s: Dictionary, l: Dictionary, m: Array) -> void:
\tstate = s.duplicate(true)
\tlabels = l
\tmembers = m
func read_field(key: String) -> Variant:
\tassert(state.has(key), key)
\treturn state[key]
func write_field(key: String, v: Variant) -> void:
\tstate[key] = v
\tevents.append(["write", key, v])
func resolve_controller_scope(_key: String) -> Variant:
\treturn state.controller_touchFloor
func sensor_hit(key: String) -> Variant:
\treturn state.sensors.get(key)
func body_hit(key: String) -> Variant:
\treturn state.body_hits.get(key)
func power_field(key: String) -> Variant:
\treturn state.power.get(key)
func goto_label(label: String, play: bool) -> void:
\tassert(labels.has(label), "Unverified missing label: " + label)
\tevents.append(["goto", label, play])
\talive = members.has(labels[label])
func controller_alive() -> bool:
\treturn alive
func effect(name: String) -> void:
\tevents.append(["effect", name])
func move_axis(name: String, v: Variant) -> void:
\tevents.append(["move_axis", name, v])
func body_call(name: String, args: Array) -> void:
\tevents.append(["body_call", name, args])
'''
RUN='''extends SceneTree
func _initialize() -> void:
\tvar input: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://input.json"))
\tvar controller = load("res://controller.gd")
\tvar adapter_class = load("res://adapter.gd")
\tvar outputs: Array = []
\tfor test in input.cases:
\t\tvar adapter = adapter_class.new(test.state, input.labels, test.hook.member_frames)
\t\tvar ai = controller.new({})
\t\tai.bind_adapter(adapter)
\t\tfor i in 3:
\t\t\tif not adapter.controller_alive():
\t\t\t\tbreak
\t\t\tai.call(test.hook.method)
\t\toutputs.append({"events": adapter.events, "alive": adapter.alive, "locals": [ai.js, ai.jumpinggg, ai.standed, ai.allF, ai.walkF]})
\tvar file = FileAccess.open("res://actual.json", FileAccess.WRITE)
\tfile.store_string(JSON.stringify(outputs, "", false, true))
\tfile.close()
\tprint("AI_CONTROLLER_NATIVE_OK ", outputs.size())
\tquit()
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--godot',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    bundle=json.loads((ROOT/'scripts/fighter/yihu.json').read_text())
    timeline=json.loads((ROOT/'data/slices/yihu-base.timeline.json').read_text())
    source=next(s['source'] for s in bundle['scripts'] if s['path']=='DefineSprite_16/frame_1/DoAction.as')
    native,meta=compile_controller(bundle,638,timeline)
    source_by_path={s['path']:s['source'] for s in bundle['scripts']}
    callbacks={h['method']:source_by_path[h['path']].replace('onClipEvent(enterFrame){','',1).rsplit('}',1)[0] for h in meta['hooks']}
    states=[]
    for test in fixtures()[::400]:
        s=test['state'].copy()
        s.update(speed=6,jumpPower=15,jumped=0,fall=False,khit=0,touch=False,gravity=3,
                 controller_touchFloor=None,body_hits={'zh20atm':len(states)%2==0})
        s['sensors']=s['sensors'].copy()
        # No absmian instance exists in the source display list. Missing lookup
        # semantics are a separate native probe; do not invent a hit in this test.
        s['sensors']['absmian']=False
        states.append(s)
    cases=[{'state':s,'hook':h} for s in states for h in meta['hooks']]
    input={'source':source,'callbacks':callbacks,'cases':cases,
           'labels':{label:f['frame'] for f in timeline['frames'] for label in f['labels']}}
    with tempfile.TemporaryDirectory(prefix='bvn-ai-dispatch-') as directory:
        tmp=Path(directory)
        (tmp/'input.json').write_text(json.dumps(input,ensure_ascii=False))
        for name,text in {'reference.cjs':NODE,'predicates.gd':compile_source(source),'controller.gd':native,
                          'adapter.gd':ADAPTER,'run.gd':RUN,'project.godot':'config_version=5\n[application]\nconfig/name="BVN AI dispatch probe"\n'}.items():
            (tmp/name).write_text(text)
        subprocess.run(['node',str(tmp/'reference.cjs'),str(tmp)],check=True)
        result=subprocess.run([str(args.godot),'--headless','--path',str(tmp),'--log-file',str(tmp/'engine.log'),'--script','run.gd'],text=True,capture_output=True,timeout=60)
        (args.output/'native.log').write_text(result.stdout+result.stderr)
        if result.returncode or 'SCRIPT ERROR' in result.stderr or not (tmp/'actual.json').exists():
            raise RuntimeError('Inspect '+str(args.output/'native.log'))
        expected=json.loads((tmp/'expected.json').read_text());actual=json.loads((tmp/'actual.json').read_text())
        differences=[{'case':cases[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
        report={'status':'passed' if not differences and len(actual)==len(expected) else 'failed',
                'cases':len(cases),'hooks':len(meta['hooks']),'differences':differences[:5],
                'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                'controller_sha256':hashlib.sha256(native.encode()).hexdigest(),
                'scope':'ordered callback translation with measured removal rule; effects and geometry are test doubles'}
        (args.output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k!='differences'}))
        if report['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()

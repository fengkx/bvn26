"""Compare native BODY functions with retained source on deterministic states.

External effects/platform queries are explicit event-recording host doubles.
This checks source translation, not end-to-end combat or Flash scheduling.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_body import FIELDS, FUNCTION, NAMES, compile_body

NODE = r'''
const fs=require('fs'),vm=require('vm');
const input=JSON.parse(fs.readFileSync(process.argv[2]+'/input.json','utf8'));
const all=input.cases.map(test=>{
 const state=structuredClone(test.state), events=[], timers=[];
 const read=k=>state[k]===null?undefined:state[k];
 const write=(k,v)=>{state[k]=v;events.push(['write',k,v??null]);};
 function object(fields,base={}){
  for(const [prop,key] of Object.entries(fields))Object.defineProperty(base,prop,{get:()=>read(key),set:v=>write(key,v)});
  return base;
 }
 const opponent=object({_x:'opponent_x',_xscale:'opponent_xscale',vecx:'opponent_vecx',heavy:'opponent_heavy'},
  {getDepth:()=>state.opponent_depth,moveX:v=>events.push(['move',true,'moveX',v]),moveY:v=>events.push(['move',true,'moveY',v])});
 opponent.mc=object({'动作':'opponent_action',sw:'opponent_sw',airBody:'opponent_airBody'},{bdmn:{}});
 const parent=object({_x:'x',_y:'y',_xscale:'xscale',scale_X:'scale_X',vecx:'vecx',heavy:'heavy'},
  {isNaruto:state.is_naruto,getDepth:()=>state.depth,swapDepths:()=>events.push(['swap_depths']),moveX:v=>events.push(['move',false,'moveX',v]),moveY:v=>events.push(['move',false,'moveY',v]),showdow:v=>events.push(['shadow',v])});
 Object.defineProperty(parent,'useAI',{get:()=>read('useAI')});
 const root=object({zhanting:'root_paused',floorY:'floorY',mapSizeX:'mapSizeX',zhongli:'gravity',wudi:'root_wudi',modo:'modo'},
  {game:{p1:opponent},bsd:(pn,xg,face)=>events.push(['start',xg,face]),bsw:(pn,face)=>events.push(['end',face]),
   addChildXG:(owner,label,x,y)=>events.push(['child_effect',label,x,y]),addStgHit:(pn,label,params)=>events.push(['stage_hit',label,params])});
 for(const [index,p] of Object.entries(state.platforms))root.game['ban'+index]={_x:p.x,_y:p.y,_width:p.width};
 const context={_parent:parent,_root:root,pn:1,isNaN,trace:()=>events.push(['trace_init',read('modo'),read('useAI')]),
  setTimeout:(callback,delay)=>{events.push(['defer',delay]);timers.push(callback);},
  gotoAndStop:l=>events.push(['goto',l,false]),gotoAndPlay:l=>events.push(['goto',l,true]),play:()=>events.push(['play']),
  bdmn:{hitTest:()=>state.body_hit}};
 for(const key of input.fields)Object.defineProperty(context,key,{get:()=>read(key),set:v=>write(key,v),configurable:true});
 for(const name of input.services)context[name]=()=>{events.push(['service',name]);return name==='isHitBan'?state.ban_y:undefined;};
 vm.createContext(context);vm.runInContext(input.source,context);
 const result=context[test.name](...test.args);
 if(test.fire_timers)for(const timer of timers)timer();
 return {result:result??null,state,events};
});
fs.writeFileSync(process.argv[2]+'/expected.json',JSON.stringify(all));
'''

ADAPTER = '''extends RefCounted
var state: Dictionary
var events: Array = []
var timers: Array = []
func _init(s: Dictionary) -> void:
\tstate = s.duplicate(true)
func read_field(key: String) -> Variant:
\tassert(state.has(key), key)
\treturn state[key]
func write_field(key: String, v: Variant) -> void:
\tstate[key] = v
\tevents.append(["write", key, v])
func body_hit(_key: String) -> Variant:
\treturn state.body_hit
func body_service(name: String) -> Variant:
\tevents.append(["service", name])
\treturn state.ban_y if name == "isHitBan" else null
func platform(index: Variant) -> Variant:
\treturn index if state.platforms.has(str(int(index))) else null
func platform_field(index: Variant, key: String) -> Variant:
\treturn state.platforms[str(int(index))][key]
func trace_init(mode: Variant, use_ai: Variant) -> void:
\tevents.append(["trace_init", mode, use_ai])
func swap_depths() -> void:
\tevents.append(["swap_depths"])
func child_effect(label: String, x: Variant, y: Variant) -> void:
\tevents.append(["child_effect", label, x, y])
func stage_hit(label: String, params: Dictionary) -> void:
\tevents.append(["stage_hit", label, params])
func defer_body(method: String, delay: Variant) -> void:
\tevents.append(["defer", delay])
\ttimers.append(method)
func goto_label(label: String, play: bool) -> void:
\tevents.append(["goto", label, play])
func play_body() -> void:
\tevents.append(["play"])
func move_body(other: bool, axis: String, v: Variant) -> void:
\tevents.append(["move", other, axis, v])
func shadow(color: Dictionary) -> void:
\tevents.append(["shadow", color])
func super_start(xg: String, face: bool) -> void:
\tevents.append(["start", xg, face])
func super_end(face: bool) -> void:
\tevents.append(["end", face])
'''

RUN = '''extends SceneTree
func _initialize() -> void:
\tvar input: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://input.json"))
\tvar body_class = load("res://body.gd")
\tvar adapter_class = load("res://adapter.gd")
\tvar outputs: Array = []
\tfor test: Dictionary in input.cases:
\t\tvar adapter = adapter_class.new(test.state)
\t\tvar body = body_class.new({})
\t\tbody.adapter = adapter
\t\tvar result = body.callv(test.name, test.args)
\t\tif test.fire_timers:
\t\t\tfor method: String in adapter.timers:
\t\t\t\tbody.call(method)
\t\toutputs.append({"result": result, "state": adapter.state, "events": adapter.events})
\tvar file = FileAccess.open("res://actual.json", FileAccess.WRITE)
\tfile.store_string(JSON.stringify(outputs, "", false, true))
\tfile.close()
\tprint("AI_BODY_NATIVE_OK ", outputs.size())
\tquit()
'''


def cases() -> list[dict]:
    baseline = dict.fromkeys(FIELDS, 0)
    baseline.update(hp=1000, sw=False, ql=200, dashQL=50, 动作=1, goran=130,
                    hitBan=False, touch=True, dashX=10, dashY=0, dashing=False,
                    htx=5, yup=2, tdtime=15, canhit=True, airBody=False, hitNear=False,
                    x=300, y=-25, xscale=100, scale_X=1, vecx=0, heavy=2,
                    opponent_x=450, opponent_xscale=-100, opponent_action=0,
                    opponent_sw=False, opponent_airBody=False, opponent_vecx=0,
                    opponent_heavy=2, root_paused=False, floorY=-25, mapSizeX=1000,
                    gravity=10, body_hit=False, ban_y=0, _lastX=300,
                    platforms={}, root_wudi=False, modo=2, useAI=True,
                    is_naruto=False, depth=1, opponent_depth=2, hurtSkling=False)
    states = [baseline]
    boundaries = {
        'hp': [-1, 0, 1], 'sw': [None, True], 'ql': [0, 49, 50, 99, 100, 301],
        'opponent_sw': [None, True], 'opponent_action': [-1, 1, 2, 3],
        '动作': [-1, 0, 2, 3], 'goran': [None, 0, 29.5, 30, 39.5, 40, 120, 120.5, 139.5, 140],
        'touch': [None, False], 'hitBan': [True], 'time': [0, 5, 6, 13, 14, 15, 16],
        'hstm': [18, 19, 20], 'dashF': [8, 9, 10], 'dashY': [-14, 12], 'dashing': [True],
        'yup': [-2, 0], 'hitNear': [True], 'hited': [1], 'tdtime': [None, 0, 1, 30],
        'root_paused': [True, None], 'wdFrameX': [None, 1, 10], 'wdFrame': [None, 9, 10],
        'x': [19, 971], 'y': [-100, -35, -34.5, -24], 'jump': [1], 'jumped': [1, 2],
        'body_hit': [True], 'ban_y': [-50], 'opponent_heavy': [0, 10],
        'opponent_vecx': [10], '_lastX': [260, 290, 310, 340],
        'root_wudi': [True], 'modo': [None, 1], '_initwudi': [True],
    }
    states += [dict(baseline, **{key: value}) for key, values in boundaries.items() for value in values]
    # Cross conditions lock the source's later assignment overriding its first.
    states += [dict(baseline, **{'动作': action, 'opponent_action': other, 'goran': r})
               for action, other, r in itertools.product([0, 1, 2], [-1, 0, 1, 3], [0, 29, 30, 39, 120, 121, 139, 140])]
    states += [dict(baseline, x=x, y=y, platforms={'2': {'x': 300, 'y': -50, 'width': 100},
                                                '3': {'x': 300, 'y': -50, 'width': 100}})
               for x, y in itertools.product([299, 300, 350, 400, 401], [-61, -60, -59, -50, -49])]
    states += [dict(baseline, is_naruto=naruto, goran=0, hurtSkling=active, depth=depth)
               for naruto, active, depth in itertools.product([False, True], [False, True], [1, 3])]
    return [{'name': name, 'state': state, 'args': args, 'fire_timers': fire}
            for state in states for name in NAMES
            for args in ([[], [True]] if name in ('beidax', 'updateDirect') else [[]])
            for fire in ([False, True] if name in ('beidax', 'doHurtSkill') else [False])]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    bundle = json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())
    native, metadata = compile_body(bundle, 638)
    source = next(s['source'] for s in bundle['scripts'] if s['path'] == metadata['path'])
    functions = {m[1]: m[0] for m in FUNCTION.finditer(source.replace('\r\n', '\n'))}
    inputs = {'source': '\n'.join(functions[n] for n in NAMES), 'fields': sorted(FIELDS),
              'services': metadata['host_services'], 'cases': cases()}
    with tempfile.TemporaryDirectory(prefix='bvn-body-') as directory:
        tmp = Path(directory)
        for name, content in {'body.gd': native, 'reference.cjs': NODE, 'adapter.gd': ADAPTER,
                              'run.gd': RUN, 'project.godot': 'config_version=5\n',
                              'input.json': json.dumps(inputs, ensure_ascii=False)}.items():
            (tmp / name).write_text(content)
        subprocess.run(['node', str(tmp / 'reference.cjs'), directory], check=True)
        result = subprocess.run([str(args.godot), '--headless', '--path', directory,
                                 '--log-file', str(args.output / 'engine.log'), '--script', 'res://run.gd'],
                                capture_output=True, text=True, timeout=90)
        log = result.stdout + result.stderr
        (args.output / 'native.log').write_text(log)
        if result.returncode or 'SCRIPT ERROR' in log or 'AI_BODY_NATIVE_OK' not in log:
            raise SystemExit(log)
        expected = json.loads((tmp / 'expected.json').read_text())
        actual = json.loads((tmp / 'actual.json').read_text())
        differences = [{'case': i, 'input': inputs['cases'][i], 'expected': e, 'actual': a}
                       for i, (e, a) in enumerate(zip(expected, actual)) if e != a]
        if len(expected) != len(actual):
            raise ValueError('Missing native outputs')
        report = {'status': 'failed' if differences else 'passed', 'cases': len(expected),
                  'differences': len(differences), 'source': metadata,
                  'generated_sha256': hashlib.sha256(native.encode()).hexdigest(),
                  'fixtures_sha256': hashlib.sha256((tmp / 'input.json').read_bytes()).hexdigest(),
                  'godot_sha256': hashlib.sha256(args.godot.read_bytes()).hexdigest(),
                  'limits': 'External effects and platform queries are host doubles; no combat parity claim.'}
        (args.output / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        (args.output / 'differences.json').write_text(json.dumps(differences[:10], ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(report, ensure_ascii=False))
        if differences:
            raise SystemExit(1)


if __name__ == '__main__':
    main()

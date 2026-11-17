"""Compare hit state transfer and target selection with retained Sprite 2 code."""
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
from compile_ai_hit_state import FUNCTION, compile_transfer

NODE = r'''
const fs=require('fs'),vm=require('vm'),dir=process.argv[2];
const input=JSON.parse(fs.readFileSync(dir+'/input.json','utf8'));
const results=input.cases.map(test=>{
 const state=structuredClone(test.state);let target={};
 const parent=new Proxy({gotoAndPlay:label=>{target={label,play:true};}}, {
  get:(o,k)=>k in o?o[k]:state[k],set:(o,k,v)=>{state[k]=v;return true;}
 });
 const context={_parent:parent,isNaN,checkHit:()=>Object.keys(test.packet).length?test.packet:undefined};
 vm.createContext(context);vm.runInContext(input.source,context);
 context[test.guard?'fangyu':'beida']();
 return {state,target};
});
const gates=input.gates.map(test=>{
 const context={gameRunning:()=>test.running,_parent:{canhit:test.canhit===null?undefined:test.canhit,pn:1},
  _root:{game:{p1:{mc:{}}}},_fsArray:[],getHitObj:()=>({hit:true})};
 vm.createContext(context);vm.runInContext(input.guard_source,context);
 return context.checkHit()!=null;
});
fs.writeFileSync(dir+'/expected.json',JSON.stringify({transfers:results,gates},
  (_key,value)=>value===undefined?null:value));
'''

RUN = '''extends SceneTree
func _initialize() -> void:
\tvar input: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://input.json"))
\tvar code = load("res://transfer.gd")
\tvar results: Array = []
\tfor test: Dictionary in input.cases:
\t\tvar state: Dictionary = test.state.duplicate(true)
\t\tvar transfer = code.new(state)
\t\tvar target = transfer.transfer(test.packet, test.guard)
\t\tresults.append({"state": state, "target": target})
\tvar gates: Array = []
\tfor test: Dictionary in input.gates:
\t\tvar gate = code.new({"canhit": test.canhit})
\t\tgates.append(gate.allows_hit(test.running))
\tvar file = FileAccess.open("res://actual.json", FileAccess.WRITE)
\tfile.store_string(JSON.stringify({"transfers": results, "gates": gates}, "", false, true))
\tfile.close()
\tprint("AI_HIT_STATE_NATIVE_OK ", results.size())
\tquit()
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    bundle = json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())
    code, metadata = compile_transfer(bundle)
    source = next(s['source'] for s in bundle['scripts'] if s['path'] == metadata['path'])
    functions = {m[1]: m[0] for m in FUNCTION.finditer(source.replace('\r\n', '\n'))}
    packets = [{}]
    for strength, duration, reaction in itertools.product([0, 5, 10, 11, 15, 25], [0, 10, 33, 100, 250], ['被打', '击飞']):
        packets.append({'pw': 80, 'zl': strength, 'yup': -2, 'hitx': 7, 'hdtime': duration, 'htype': reaction})
    packets.append({'pw': 80, 'zl': 5, 'yup': 2, 'hitx': 7, 'htype': '被打'})
    # Rifagu gjl2.cbs2 supplies only damage and duration; absent operands
    # must survive the transfer instead of inventing a reaction or impulse.
    packets.append({'pw': 0, 'hdtime': 5000})
    cases = [{'packet': packet, 'guard': guard, 'state': {'time': 7, 'yup': 3, 'htx': 4, 'bdzl': 0, 'tdtime': 5, 'jhp': 0}}
             for packet, guard in itertools.product(packets, [False, True])]
    gates = [{'running': running, 'canhit': canhit} for running, canhit in itertools.product([False, True], [None, False, True, 0, 1])]
    inputs = {'source': functions['beida'] + '\n' + functions['fangyu'], 'cases': cases,
              'guard_source': functions['checkHit'], 'gates': gates}
    with tempfile.TemporaryDirectory(prefix='bvn-hit-state-') as directory:
        tmp = Path(directory)
        for name, content in {'transfer.gd': code, 'reference.cjs': NODE, 'run.gd': RUN,
                              'project.godot': 'config_version=5\n', 'input.json': json.dumps(inputs, ensure_ascii=False)}.items():
            (tmp / name).write_text(content)
        subprocess.run(['node', str(tmp / 'reference.cjs'), directory], check=True)
        run = subprocess.run([str(args.godot), '--headless', '--path', directory, '--log-file', str(args.output / 'engine.log'),
                              '--script', 'res://run.gd'], capture_output=True, text=True, timeout=60)
        log = run.stdout + run.stderr
        (args.output / 'native.log').write_text(log)
        if run.returncode or 'SCRIPT ERROR' in log or 'AI_HIT_STATE_NATIVE_OK' not in log:
            raise SystemExit(log)
        expected = json.loads((tmp / 'expected.json').read_text())
        actual = json.loads((tmp / 'actual.json').read_text())
        if actual != expected:
            differences = {'expected': expected, 'actual': actual}
            (args.output / 'differences.json').write_text(json.dumps(differences, ensure_ascii=False, indent=2))
            raise SystemExit('Hit state translation differs')
        report = {'status': 'passed', 'cases': len(cases), 'guard_cases': len(gates), 'source': metadata,
                  'generated_sha256': hashlib.sha256(code.encode()).hexdigest(),
                  'fixtures_sha256': hashlib.sha256((tmp / 'input.json').read_bytes()).hexdigest(),
                  'godot_sha256': hashlib.sha256(args.godot.read_bytes()).hexdigest()}
        (args.output / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()

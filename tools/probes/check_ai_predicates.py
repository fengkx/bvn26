"""Compare native compiled predicates with the retained scalar source in Node.

This checks compiler translation, not Flash scheduling or MovieClip hitTest.
Sensors are supplied booleans and undefined is represented as JSON null only at
this fixture boundary. Explicit AS2 null and string-to-number coercion are outside
this typed battle-context ABI. No fixture result is a full-game parity claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_predicates import NAMES, compile_source

NODE = r'''
const fs = require('fs'), vm = require('vm');
const [sourcePath, casesPath, outputPath] = process.argv.slice(2);
const source = fs.readFileSync(sourcePath, 'utf8');
const cases = JSON.parse(fs.readFileSync(casesPath, 'utf8'));
const results = cases.map(test => {
  const s = test.state;
  const body = {pn:2};
  for (const key of ['attran','defran','goran','jumpran','bisharan','touchFloor','ql','canhit','sw'])
    body[key] = s[key] === null ? undefined : s[key];
  body._parent = {useAI:true, _x:s.x, _y:s.y, scale_X:s.scale_X, _xscale:s.xscale, _curGJL:s.power};
  body.AImain = {};
  for (const key of ['kanmian','tkanmian','zh1mian','zh2mian','zh3mian','kj1mian','kj2mian','bsmian','sbsmian','absmian','cbsmian'])
    body.AImain[key] = {hitTest:()=>s.sensors[key] ?? undefined};
  const context = {_parent:body, _root:{zhanting:s.root_paused ?? undefined, game:{
    p2:{_x:s.opponent_x,_y:s.opponent_y,mc:{动作:s.opponent_action,sw:s.opponent_sw ?? undefined,bdmn:{}}},
    p2fz:{动作:s.opponent_helper_action}
  }}, isNaN};
  vm.createContext(context);
  vm.runInContext(source, context);
  const value = context[test.name](...test.args);
  return {value, scale_X:body._parent.scale_X,xscale:body._parent._xscale};
});
fs.writeFileSync(outputPath, JSON.stringify(results));
'''
GODOT = '''extends SceneTree
func _initialize() -> void:
\tvar cases: Array = JSON.parse_string(FileAccess.get_file_as_string("res://cases.json"))
\tvar compiled = load("res://predicates.gd")
\tvar results: Array = []
\tfor test in cases:
\t\tvar state: Dictionary = test.state.duplicate(true)
\t\tvar ai = compiled.new(state)
\t\tvar value: Variant = ai.callv(test.name, test.args)
\t\tresults.append({"value": value, "scale_X": state.scale_X, "xscale": state.xscale})
\tvar file = FileAccess.open("res://actual.json", FileAccess.WRITE)
\tfile.store_string(JSON.stringify(results))
\tfile.close()
\tprint("AI_PREDICATES_NATIVE_OK ", results.size())
\tquit()
'''


def fixtures() -> list[dict]:
    rng = random.Random(2605)
    bounds = [None, 0, 30, 40, 50, 55, 60, 70, 80, 90, 95, 100, 120, 130, 140, 150, 200, 220, 250, 300, 500]
    samples = [None] + [v + d for v in bounds[1:] for d in (-0.01, 0, 0.01)]
    sensors = ['kanmian','tkanmian','zh1mian','zh2mian','zh3mian','kj1mian','kj2mian','bsmian','sbsmian','absmian','cbsmian']
    moves = ['zh1','zh2','zh3','kj1','kj2','bs','sbs','kbs','cbs','tz']
    cases = []
    # Every threshold is exercised in every opponent state with both sensor
    # outcomes. Independent random values then cover interactions among fields.
    states = []
    for sample in samples:
        for action in (-1, 0, 1, 2, 3):
            for hit in (False, True):
                state = {key:sample for key in ('attran','defran','goran','jumpran','bisharan')}
                state.update(opponent_action=action, opponent_helper_action=rng.choice((0,1)),
                             x=rng.choice((-100,-20,0,20,100)),y=0,opponent_x=0,
                             opponent_y=rng.choice((-20.01,-20,0,50,50.01)),scale_X=1,xscale=100,
                             root_paused=rng.choice((None,False,True)),opponent_sw=False,
                             touchFloor=rng.choice((None,False,True)),canhit=rng.choice((None,False,True)),
                             sw=rng.choice((None,False,True)),ql=rng.choice((99,100,299,300)),
                             sensors={key:hit for key in sensors},power={key+'zl':rng.choice((10,11)) for key in moves})
                states.append(state)
    for _ in range(200):
        state = dict(rng.choice(states))
        for key in ('attran','defran','goran','jumpran','bisharan'):
            state[key] = rng.choice(samples)
        states.append(state)
    for state in states:
        for name in NAMES:
            args_sets = [[]]
            if name == 'isPoFangAct':
                args_sets = [['tz'], ['missing']]
            elif name == 'combohitAI':
                args_sets += [['zh1']]
            elif name in ('airhit','airMagichit','nornalhit','magichit1','magichit2','magichit3','skill1','skill2'):
                args_sets += [[True], [False], [1]]
            elif name.startswith('bisha'):
                args_sets += [[True], [False,99], [True,300]]
            for args in args_sets:
                cases.append({'state':state, 'name':name, 'args':args})
    return cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--godot', required=True, type=Path)
    parser.add_argument('--node', default='node')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    bundle = json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())
    source = next(s['source'] for s in bundle['scripts'] if s['path'] == 'DefineSprite_16/frame_1/DoAction.as')
    cases = fixtures()
    with tempfile.TemporaryDirectory(prefix='bvn-ai-predicates-') as directory:
        tmp = Path(directory)
        (tmp/'source.js').write_text(source)
        (tmp/'reference.cjs').write_text(NODE)
        (tmp/'cases.json').write_text(json.dumps(cases))
        (tmp/'predicates.gd').write_text(compile_source(source))
        (tmp/'run.gd').write_text(GODOT)
        (tmp/'project.godot').write_text('config_version=5\n[application]\nconfig/name="AI predicates"\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="'+str(tmp/'userdata')+'"\n')
        subprocess.run([args.node,str(tmp/'reference.cjs'),str(tmp/'source.js'),str(tmp/'cases.json'),str(tmp/'expected.json')],check=True)
        result = subprocess.run([str(args.godot),'--headless','--path',str(tmp),'--log-file',str(tmp/'engine.log'),'--script','run.gd'],text=True,capture_output=True,timeout=90)
        (args.output/'native.log').write_text(result.stdout + result.stderr)
        if result.returncode or 'SCRIPT ERROR' in result.stderr or not (tmp/'actual.json').exists():
            raise RuntimeError('Native predicate test failed; inspect '+str(args.output/'native.log'))
        expected = json.loads((tmp/'expected.json').read_text())
        actual = json.loads((tmp/'actual.json').read_text())
        differences = [{'index':i,'case':cases[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a != b]
        report = {'status':'passed' if not differences and len(actual)==len(expected) else 'failed',
                  'cases':len(cases),'actual':len(actual),'differences':differences[:20],
                  'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                  'generated_sha256':hashlib.sha256((tmp/'predicates.gd').read_bytes()).hexdigest(),
                  'fixtures_sha256':hashlib.sha256((tmp/'cases.json').read_bytes()).hexdigest(),
                  'godot_sha256':hashlib.sha256(args.godot.read_bytes()).hexdigest(),
                  'scope':'native compiler scalar equivalence; no Flash scheduling, sensor geometry or battle acceptance'}
        (args.output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k!='differences'}))
        if report['status'] != 'passed':
            raise SystemExit(1)


if __name__ == '__main__':
    main()

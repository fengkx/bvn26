"""Build input-driven cases from compiled, source-linked command catalogs.

A case is a fresh fight. Fixture coordinates and energy are setup, never expected
results; only native Flash traces can establish behavioral expectations.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEYS = {
    'p1': dict(zip(['up','down','left','right','attack','jump','dash','ranged','special','summon'], ['w','s','a','d','j','k','l','u','i','o'])),
    'p2': dict(zip(['up','down','left','right','attack','jump','dash','ranged','special','summon'], ['上箭','下箭','左箭','右箭','N1','N2','N3','N4','N5','N6'])),
}
COMMANDS = {
    'nornalhit':['attack'], 'skill1':['down','attack'], 'skill2':['up','attack'],
    'magichit1':['ranged'], 'magichit2':['down','ranged'], 'magichit3':['up','ranged'],
    'bisha':['special'], 'bishaUP':['up','special'], 'bishaSuper':['down','special'],
    'airhit':['attack'], 'airMagichit':['ranged'], 'bishaAir':['special'],
    'zhaoHuan':['summon'], 'wankai':['attack','jump'], 'rush':['dash'],
    'jump':['jump'], 'jumpDown':['down','jump'], 'defence':['down'],
}

def window(slot, keys, start, end):
    return {'slot':slot, 'keys':keys, 'start':start, 'end':end}


def generate(fighters=None, exclude_commands=()):
    cases = []
    for fighter, slot in fighters or [('minren','p1'),('yihu','p2')]:
        other = 'p2' if slot == 'p1' else 'p1'
        catalog = json.loads((ROOT / f'godot/generated/fighters/{fighter}/combat.json').read_text())['command_catalog']
        for entry in catalog['entries']:
            command = entry.get('slot')
            if command not in COMMANDS or command in exclude_commands:
                continue
            air = command in ['airhit','airMagichit','bishaAir','jumpDown'] or entry['label'] == '跳2'
            scenarios = ['neutral','held','guard','mirror','wall','air_target','trade','dash_twice']
            minimum = entry.get('energy_min') or 0
            if minimum:
                scenarios += ['energy_below','energy_exact','energy_above']
            for scenario in scenarios:
                energy = {'energy_below':minimum-1,'energy_exact':minimum,'energy_above':minimum+1}.get(scenario,300)
                setup = {'p1':{'x':300,'energy':300},'p2':{'x':350,'energy':300}}
                setup[slot]['energy'] = energy
                if scenario == 'mirror': setup['p1']['x'], setup['p2']['x'] = 350,300
                if scenario == 'wall': setup['p1']['x'], setup['p2']['x'] = 20,70
                inputs = []
                start = 20 if air else 10
                if air: inputs.append(window(slot,['jump'],5,6))
                inputs.append(window(slot, COMMANDS[command],start,start+(100 if scenario=='held' else 3)))
                if scenario == 'guard': inputs.append(window(other,['down'],1,300))
                if scenario == 'air_target': inputs.append(window(other,['jump'],5,6))
                if scenario == 'trade': inputs.append(window(other,['attack'],start,start+3))
                if scenario == 'dash_twice':
                    inputs.extend([window(other,['dash'],start,start+3),window(other,['dash'],start+12,start+15)])
                case = {'id':f'{fighter}-{entry["start_frame"] or "missing"}-{command}-{scenario}',
                    'fighter':fighter,'slot':slot,'label':entry['label'],'scenario':scenario,
                    'frames':300,'setup':setup,'inputs':inputs,
                    'target_frames':[entry['start_frame'],entry['end_frame']],
                    'has_source_timeline':entry['has_timeline'],
                    'source_dispatch':entry.get('source_dispatch'), 'status':'not_run'}
                if fighter not in ['minren', 'yihu']:
                    case['fighters'] = {slot: fighter, other: 'yihu' if slot == 'p1' else 'minren'}
                cases.append(case)
    return cases


def encode_case(case, run_id):
    from urllib.parse import urlencode
    values = {'run_id':run_id, 'case_id':case['id']}
    for slot, setup in case['setup'].items():
        values[slot+'x'] = setup['x']
        values[slot+'energy'] = setup['energy']
    values['windows'] = ';'.join(f"{item['start']}:{item['end']}:{KEYS[item['slot']][key]}"
                               for item in case['inputs'] for key in item['keys'])
    return urlencode(values)


def source_fixture(case):
    lines = ['   if(aiFight == 0)', '   {', '      clearInterval(_root.airanset);']
    for slot, values in case['setup'].items():
        if slot not in KEYS: raise ValueError('Invalid player slot')
        lines += [f'      _root.game.{slot}.mc.gotoAndPlay("站立");',
                  f'      _root.game.{slot}._x = {float(values["x"])};',
                  f'      _root.game.{slot}.mc.ql = {float(values["energy"])};']
    lines += ['   }', '   aiHeld = {};']
    for item in case['inputs']:
        assignments = ' '.join(f'aiHeld[{KEYS[item["slot"]][key]}] = true;' for key in item['keys'])
        lines.append(f'   if(aiFight >= {int(item["start"])} && aiFight < {int(item["end"])}) {{ {assignments} }}')
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fighter', help='Generate one fighter in the P1 slot')
    parser.add_argument('--exclude-command', action='append', default=[])
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    cases=generate([(args.fighter, 'p1')] if args.fighter else None, args.exclude_command)
    for case in cases: (args.output/(case['id']+'.json')).write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'status':'generated_not_validated'}))

if __name__=='__main__': main()

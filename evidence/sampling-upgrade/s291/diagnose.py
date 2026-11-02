"""Bounded structural correspondence, explicitly conditional on observer erasure."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REGISTER_MAP = {0: 0, 2: 1, 3: 2, 4: 6, 5: 4, 6: 3, 7: 8,
                8: 5, 9: 11, 10: 10, 11: 7, 12: 9}
LABELS = ['dashing', 'paused', 'own_air', 'other_air', 'displacement',
          'target', 'receiver', 'result']


def prior_module():
    spec = importlib.util.spec_from_file_location('s291_prior', HERE.parent / 's283/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reduced_graph(projection, removed, mapping):
    nodes = projection['nodes']
    kept = [i for i in range(len(nodes)) if i not in removed]
    positions = {old: new for new, old in enumerate(kept)}
    positions[len(nodes)] = len(kept)

    def resolve(index):
        while index in removed:
            if nodes[index]['successors'] != [index + 1]:
                raise ValueError('cannot erase control flow')
            index += 1
        if index not in positions:
            raise ValueError('invalid edge')
        return positions[index]

    result = []
    for i in kept:
        instruction = nodes[i]['instruction']
        match = re.fullmatch(r'(Push register|StoreRegister )(\d+)', instruction)
        if match:
            reg = int(match[2])
            if reg not in mapping:
                raise ValueError('unmapped register')
            instruction = match[1] + str(mapping[reg])
        successors = [resolve(j) for j in nodes[i]['successors']]
        if instruction.startswith(('If ', 'Jump ')):
            instruction = instruction.split()[0] + ' ' + str(successors[0])
        result.append({'instruction': instruction, 'successors': successors})
    return result, kept


def audit(original, candidate):
    a = [n['instruction'] for n in original['nodes']]
    b = [n['instruction'] for n in candidate['nodes']]
    removed, reasons = set(), []

    def erase(indices, reason):
        if removed.intersection(indices):
            raise ValueError('overlapping erasure')
        removed.update(indices)
        reasons.append({'reason': reason, 'indices': list(indices),
                        'instructions': [b[i] for i in indices]})

    # These are an explicit hypothetical projection, never executable rewriting.
    owners = [i for i, op in enumerate(b) if op == 'Push register1']
    if len(owners) != len(LABELS):
        raise ValueError('observer owner count')
    erase(owners, 'observer owner pushes; activation meaning remains unproved')
    for label in LABELS:
        pattern = [f'Push "{label}"', 'Push 3', 'Push register2',
                   'Push "s283Value"', 'CallMethod']
        matches = [i for i in range(len(b)) if b[i:i+5] == pattern]
        if len(matches) != 1:
            raise ValueError('observer envelope: ' + label)
        erase(range(matches[0], matches[0]+5), 'hypothetical pass-through: ' + label)
    for reg in (7, 8, 9, 12):
        pattern = ['Push undefined', f'StoreRegister {reg}', 'Pop']
        matches = [i for i in range(len(b)) if b[i:i+3] == pattern]
        if len(matches) != 1:
            raise ValueError('declaration envelope')
        erase(range(matches[0], matches[0]+3), f'candidate local initialization register{reg}; conditional deletion')
    # Preserve all other Not operations; only the source doDashX guard differs.
    pattern = ['Push "dashing"', 'GetVariable', 'Not', 'Not']
    matches = [i for i in range(len(a)) if a[i:i+4] == pattern]
    if len(matches) != 1:
        raise ValueError('doDashX double-Not site')
    original_removed = {matches[0]+2, matches[0]+3}
    ag, ak = reduced_graph(original, original_removed, {i:i for i in range(12)})
    bg, bk = reduced_graph(candidate, removed, REGISTER_MAP)
    if ag != bg:
        mismatch = next((i for i, (x,y) in enumerate(zip(ag,bg)) if x != y), min(len(ag),len(bg)))
        raise ValueError(f'residual instruction/control-flow mismatch at {mismatch}')
    return {
        'conditional_body_graph_equal': True,
        'original_header': original['header'], 'candidate_header': candidate['header'],
        'headers_equal': original['header'] == candidate['header'],
        'candidate_to_original_register_map': REGISTER_MAP,
        'candidate_erasure': reasons,
        'original_erasure': [{'index':i,'instruction':a[i]} for i in sorted(original_removed)],
        'original_node_count':len(a), 'candidate_node_count':len(b),
        'residual_node_count':len(ag),
        'node_correspondence': [{'original_index':x,'candidate_index':y,**n}
                                for x,y,n in zip(ak,bk,ag)],
        'register_uses': [{'candidate_register':r,'original_register':v,
                          'candidate_indices':[i for i in bk if b[i] in (f'Push register{r}',f'StoreRegister {r}')],
                          'original_indices':[i for i in ak if a[i] in (f'Push register{v}',f'StoreRegister {v}')]}
                         for r,v in REGISTER_MAP.items()],
        'assumptions_not_proved': [
            'Changed function flags/preloads bind corresponding registers to equivalent live activations.',
            's283Value is identity with no mutation, exceptions, reentrancy, lifetime or scheduling effects; no helper is installed.',
            'Deleting four candidate local initializations preserves activation-visible behavior.',
            'Deleting source double-Not before If preserves coercion behavior on actual values.'
        ]}


def verify_pins(path):
    for name, expected in json.loads(path.read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input hash mismatch: ' + name)


def diagnose():
    verify_pins(HERE / 'ranking-basis-sha256.json')
    verify_pins(HERE / 'input-sha256.json')
    prior = prior_module().diagnose()
    if prior != json.loads((HERE.parent / 's283/diagnosis.json').read_text()):
        raise ValueError('historical replay changed')
    return {
        'base':'975defcd0a9e6c80a3b938bc27ee14964e4459b8',
        'scope':'AFTER-s290 rank 1 only; P2 Sprite638 ticks10-12 static qualification',
        'production_admitted':False, 'native_parity_proven':False,
        'observer_qualified':False, 'activation_correspondence_proved':False,
        'external_callsite_execution_proved':False, 'product_obligations_closed':0,
        'new_builds':0, 'new_player_launches':0, 'new_captures':0,
        'historical_events_revalidated':prior['historical_events_revalidated'],
        'historical_execution_observed':prior['historical_execution_observed'],
        'audit':audit(prior['original_projection'], prior['candidate_projection']),
        'capture_decision':'Not authorized by this static cut; observer prerequisites remain unproved.',
        'blocker':'Conditional graph correspondence is not activation/helper/perturbation equivalence.',
        'next_discriminator':'Independently qualify the changed activation/preload mapping and all four erasure assumptions before installing a bounded helper or capturing. Keep natural executed/skipped controls and same-run operand lifetimes separate.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-observer', action='store_true')
    parser.add_argument('--require-external-callsite', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print('S291_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    if args.require_observer or args.require_external_callsite:
        print('S291_OBSERVER_UNPROVED: ' + report['blocker'])
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

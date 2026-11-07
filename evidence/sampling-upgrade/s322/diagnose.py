"""Bound activation exposure in archived body-push code; never certify live bindings."""
import argparse
from collections import deque
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = '6e67d78d0f222344dff6ab6c3ff578ad4784c979'
GATES = {name: 'S322_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('scope-binding', 'activation-erasure', 'coercion-erasure',
                      'helper-effects', 'off-on', 'external-callsite')}
CALLS = {'CallFunction', 'CallMethod', 'NewObject', 'NewMethod'}
SCOPE = {'GetVariable', 'SetVariable', 'GetMember', 'SetMember', 'DefineLocal',
         'DefineLocal2', 'With', 'Delete', 'Delete2', 'Enumerate', 'Enumerate2'}


def load_prior():
    spec = importlib.util.spec_from_file_location('s322_s312', HERE.parent / 's312/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exposure(graph, start, register):
    """All structural paths to first explicit overwrite, return or body end.

    Calls do not terminate traversal: downstream paths are conditional on normal
    continuation. Exceptional/native edges and path feasibility are not modelled.
    """
    nodes = graph['nodes']
    if type(start) is not int or not 0 <= start < len(nodes):
        raise ValueError('Invalid exposure start')
    for i, node in enumerate(nodes):
        if node['index'] != i or any(type(e) is not int or not 0 <= e <= len(nodes)
                                     for e in node['successors']):
            raise ValueError('Invalid graph identity/edge')
        if (node['instruction'] == 'Return') != (not node['successors']):
            raise ValueError('Unmodelled terminal')
    queue = deque([(start, [start])])
    seen, rows = set(), []
    while queue:
        index, path = queue.popleft()
        if index in seen:
            continue
        seen.add(index)
        if index == len(nodes):
            rows.append({'index': index, 'kind': 'body-end', 'node': None, 'path': path})
            continue
        node = nodes[index]
        kind = ('overwrite' if node['instruction'] == f'StoreRegister {register}'
                else 'return' if node['instruction'] == 'Return' else 'intermediate')
        rows.append({'index': index, 'kind': kind, 'node': node, 'path': path})
        if kind == 'intermediate':
            queue.extend((edge, path + [edge]) for edge in node['successors'])
    rows.sort(key=lambda row: row['index'])
    return {'rows': rows,
            'boundaries': {kind: [r['index'] for r in rows if r['kind'] == kind]
                           for kind in ('overwrite', 'return', 'body-end')},
            'explicit_calls': [r['index'] for r in rows if r['node'] and r['node']['instruction'] in CALLS],
            'scope_member_operations': [r['index'] for r in rows if r['node'] and r['node']['instruction'] in SCOPE]}


def audit(graphs, structural):
    original, candidate = (graphs[side + '_projection'] for side in ('original', 'candidate'))
    prior = load_prior()
    if json.loads(json.dumps(prior.load('s291').audit(original, candidate))) != structural:
        raise ValueError('Full callback correspondence changed')
    mapping = {r['candidate_index']: r['original_index'] for r in structural['node_correspondence']}
    removed = {i for e in structural['candidate_erasure'] for i in e['indices']}
    rows = []
    for envelope in structural['candidate_erasure']:
        if not envelope['reason'].startswith('candidate local initialization'):
            continue
        store = envelope['indices'][1]
        register = int(candidate['nodes'][store]['instruction'].split()[1])
        start = store + 1
        # Follow only the erased straight-line prefix to the first mapped node.
        entry = start
        while entry in removed:
            if candidate['nodes'][entry]['successors'] != [entry + 1]:
                raise ValueError('Nonlinear erased prefix')
            entry += 1
        original_register = structural['candidate_to_original_register_map'][str(register)]
        right = exposure(candidate, start, register)
        left = exposure(original, mapping[entry], original_register)
        mapped = sorted(mapping[r['index']] for r in right['rows'] if r['index'] in mapping)
        if mapped != [r['index'] for r in left['rows'] if r['node']]:
            raise ValueError('Exposure region correspondence changed')
        rows.append({'candidate_register': register, 'original_register': original_register,
                     'initializer': candidate['nodes'][store], 'original_entry': mapping[entry],
                     'candidate': right, 'original': left,
                     'activation_visible_erasure': None})
    erased = [r['index'] for r in structural['original_erasure']]
    if erased != [152, 153]:
        raise ValueError('Coercion site changed')
    # This local window identifies the read and branch, not its live value/type.
    reverse = {v: k for k, v in mapping.items()}
    coercion = {'original_window': original['nodes'][150:155],
                'candidate_window': candidate['nodes'][reverse[150]:reverse[154] + 1],
                'original_branch_edges': original['nodes'][154]['successors'],
                'candidate_branch_edges': candidate['nodes'][reverse[154]]['successors'],
                'actual_value': None, 'actual_type': None, 'coercion_effect': None}
    return {'initialization_exposure': rows, 'coercion_cut': coercion,
            'coordinates': 'Expanded archived pcode node indices, not native PCs, byte offsets or execution order.',
            'limit': 'Structural paths only. Body end is not an observed dispatcher return. No opcode is certified harmless; scope/member/coercion/exception/reentrancy/lifetime/scheduling effects remain unproved.'}


def diagnose():
    prior_module = load_prior()
    prior_module.verify_pins(HERE / 'input-sha256.json')
    prior = prior_module.diagnose()
    if json.loads(json.dumps(prior)) != json.loads((HERE.parent / 's312/diagnosis.json').read_text()):
        raise ValueError('Locked s312 replay changed')
    graphs = json.loads((HERE.parent / 's283/diagnosis.json').read_text())
    structural = json.loads((HERE.parent / 's291/diagnosis.json').read_text())['audit']
    return {'slice': 's322', 'base': BASE, 'scope': 'AFTER-s317 rank #5 only',
            'production_admitted': False, 'native_parity_proven': False,
            'm0_02_status': 'pending', 'product_obligations_closed': 0,
            'locked_s312_reproduced': True,
            'historical_events_revalidated': prior['historical_events_revalidated'],
            'historical_execution_observed': prior['historical_execution_observed'],
            'audit': audit(graphs, structural),
            'independent_live_observations': {name: None for name in
                ('defining_scope', 'this_identity', 'root_identity', 'parent_identity',
                 'activation_visibility', 'actual_coercion', 'helper_effects', 'off_on', 'external_callsite')},
            'gates': {flag: {'proved': False, 'code': code} for flag, code in GATES.items()},
            'new_builds': 0, 'new_player_launches': 0, 'new_attaches': 0,
            'new_memory_reads': 0, 'new_captures': 0, 'other_ranks_executed': [],
            'blocker': 'No independent retained invocation binds defining scope or this/root/parent generations. Static exposure and coercion windows cannot qualify activation-visible erasure. Helper and off/on controls remain blocked before installation/capture.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, IndexError) as exc:
        parser.exit(1, 'S322_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S322_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

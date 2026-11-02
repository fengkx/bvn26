"""Bound Yulong initialized-slot exposure; do not infer hidden activation behavior."""
import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '90ddc6cb245d0508eb340423bba58f80e167e01c'
GATES = {name: 'S318_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('activation-erasure', 'observer', 'nested-entry', 'parent-removal')}


def load_prior():
    spec = importlib.util.spec_from_file_location('s318_locked_s309', HERE.parent / 's309/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + name)


def frontier(graph, start, role):
    """Visit every structural path until overwrite/return; no branch feasibility model."""
    if not graph or type(start) is not int or not 0 <= start < len(graph):
        raise ValueError('Invalid start')
    for i, node in enumerate(graph):
        if node['id'] != i or any(type(e) is not int or not 0 <= e < len(graph)
                                  for e in node['edges']):
            raise ValueError('Invalid graph identity/edge')
        if (node['op'] == 'Return') != (not node['edges']):
            raise ValueError('Unmodelled terminal edge')
    pending = deque([(start, [start])])
    seen, rows = set(), []
    while pending:
        i, path = pending.popleft()
        if i in seen:
            continue
        seen.add(i)
        node = graph[i]
        kind = ('overwrite' if node['op'] == 'StoreRegister' and node['operand'] == [role]
                else 'return' if node['op'] == 'Return' else 'intermediate')
        rows.append({'node': node, 'kind': kind, 'witness_path': path})
        if kind == 'intermediate':
            pending.extend((edge, path + [edge]) for edge in node['edges'])
    rows.sort(key=lambda row: row['node']['id'])
    return {'start': start, 'rows': rows,
            'overwrites': [r['node']['id'] for r in rows if r['kind'] == 'overwrite'],
            'returns_before_overwrite': [r['node']['id'] for r in rows if r['kind'] == 'return'],
            'explicit_calls_before_overwrite': [r['node']['id'] for r in rows
                                               if r['node']['op'] in ('CallMethod', 'CallFunction', 'NewMethod', 'NewObject')],
            'opcodes_present': sorted({r['node']['op'] for r in rows})}


def audit(prior, structural):
    graphs = prior['audit']['graphs']
    # Check all nodes against the retained byte-derived decoder, not just the cut.
    for side in graphs:
        expected = load_prior().raw_graph(structural['getHitObj_audit'][side])
        if graphs[side] != expected:
            raise ValueError('Full graph changed')
    mapping = {p['archived']: p['original'] for p in structural['getHitObj_audit']['node_pairs']}
    if len(mapping) != 80 or len(set(mapping.values())) != 80:
        raise ValueError('Conditional correspondence changed')
    decoder = load_prior().load_prior()
    left = decoder.graph(structural['getHitObj_audit']['original'])['nodes']
    right = decoder.graph(structural['getHitObj_audit']['s275_archive'], erase_initializers=True)['nodes']
    if set(mapping) != set(right) or set(mapping.values()) != set(left):
        raise ValueError('Incomplete conditional correspondence')
    for archived, original in mapping.items():
        a, b = right[archived], left[original]
        if (a['op'], a['operand'], [mapping[e] for e in a['edges']]) != (b['op'], b['operand'], b['edges']):
            raise ValueError('Conditional node/edge correspondence changed')
    # The shared array push after both initializers is the original region entry.
    if mapping.get(14) != 8 or graphs['original'][8]['operand'] != ['register', 'array']:
        raise ValueError('Shared cut entry changed')
    results = []
    for role, initializer in (('_loc2_', 9), ('_loc4_', 12)):
        node = graphs['s275_archive'][initializer]
        if node['op'] != 'StoreRegister' or node['operand'] != [role] or node['edges'] != [initializer + 1]:
            raise ValueError('Initializer changed')
        candidate = frontier(graphs['s275_archive'], initializer + 1, role)
        original = frontier(graphs['original'], 8, role)
        mapped = sorted(mapping[r['node']['id']] for r in candidate['rows'] if r['node']['id'] in mapping)
        original_ids = sorted(r['node']['id'] for r in original['rows'])
        if mapped != original_ids:
            raise ValueError('Exposure region correspondence changed')
        boundaries = {}
        for key in ('overwrites', 'returns_before_overwrite', 'explicit_calls_before_overwrite'):
            boundaries[key] = [{'archive': i, 'original': mapping[i]} for i in candidate[key]]
            if sorted(mapping[i] for i in candidate[key]) != original[key]:
                raise ValueError('Boundary correspondence changed')
        results.append({'role': role, 'initializer': node,
                        'original': original, 's275_archive': candidate,
                        'mapped_region_nodes': mapped,
                        'unmapped_archive_nodes': [r['node']['id'] for r in candidate['rows']
                                                   if r['node']['id'] not in mapping],
                        'boundaries': boundaries,
                        'activation_visible_effect': None})
    return {'rows': results,
            'coordinates': 'Expanded decoded nodes and uncompressed SWF offsets; not native PCs or executed order.',
            'limit': 'All graph edges are considered without path feasibility. Explicit stores terminate the region; no claim about slot aliases, hidden access, enumeration/member/coercion effects, exceptions, reentrancy, timing or native return. No opcode is classified harmless.'}


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'ranking-basis-sha256.json')
    prior = load_prior().diagnose()
    if json.loads(json.dumps(prior)) != json.loads((HERE.parent / 's309/diagnosis.json').read_text()):
        raise ValueError('Locked s309 replay changed')
    structural = json.loads((HERE.parent / 's302/diagnosis.json').read_text())
    return {'slice': 's318', 'base': BASE, 'scope': 'AFTER-s317 rank #1 only',
            'production_admitted': False, 'native_parity_proven': False,
            'm0_02_status': 'pending', 'product_obligations_closed': 0,
            'locked_s309_reproduced': True, 'retained_events': prior['retained_events'],
            'audit': audit(prior, structural),
            'observations': prior['observations'],
            'gates': {flag: {'proved': False, 'code': code} for flag, code in GATES.items()},
            'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0,
            'other_ranks_executed': [],
            'blocker': 'Initialized slots can reach the structural null-return path without overwrite. No explicit call in these regions does not establish hidden activation invisibility. Live slot/scope binding and independent enumeration/member/coercion/return-boundary effects remain absent; observer and nested/removal controls remain unqualified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, IndexError) as exc:
        parser.exit(1, 'S318_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S318_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Audit explicit local definitions in the locked Yulong getHitObj functions."""
import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '93a45fa5a6a034b4125f6a984bb24639f18b6ff5'
ROLES = ('_loc2_', '_loc4_')


def load_prior():
    spec = importlib.util.spec_from_file_location('s309_locked_s302', HERE.parent / 's302/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, expected in json.loads(path.read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('hash mismatch: ' + name)


def raw_graph(nodes):
    """Keep all jumps, Boolean operations and initializers; assume no path feasibility."""
    graph = []
    for i, node in enumerate(nodes):
        if node['id'] != i:
            raise ValueError('invalid node identity')
        if node['op'] == 'Return':
            edges = []
        elif node['op'] == 'Jump':
            edges = [node['target']]
        elif node['op'] == 'If':
            edges = [node['target'], i + 1]
        else:
            edges = [i + 1]
        if any(type(e) is not int or not 0 <= e < len(nodes) for e in edges):
            raise ValueError('invalid graph edge')
        graph.append({**node, 'edges': edges})
    if not graph:
        raise ValueError('empty function')
    return graph


def reaching_reads(graph, role):
    """Finite (node, last explicit store) traversal; -1 means unknown entry value."""
    pending = deque([(0, -1, [0])])
    visited, witnesses = set(), {}
    while pending:
        i, definition, path = pending.popleft()
        state = (i, definition)
        if state in visited:
            continue
        visited.add(state)
        node = graph[i]
        if node['op'] == 'Push' and node['operand'] == ['register', role]:
            witnesses.setdefault(i, {})[definition] = path
        outgoing = i if node['op'] == 'StoreRegister' and node['operand'] == [role] else definition
        pending.extend((e, outgoing, path + [e]) for e in node['edges'])
    return [{'read': i, 'offset': graph[i]['offset'],
             'definitions': sorted(defs),
             'witnesses': [{'definition': d, 'path': defs[d]} for d in sorted(defs)]}
            for i, defs in sorted(witnesses.items())]


def audit(locked):
    prior = load_prior()
    decoded = locked['getHitObj_audit']
    # Recompute the conditional bijection, but perform dataflow on unprojected nodes.
    left, right = decoded['original'], decoded['s275_archive']
    if json.loads(json.dumps(prior.graph(left))) != decoded['original_projection']:
        raise ValueError('original projection changed')
    if json.loads(json.dumps(prior.graph(right, erase_initializers=True))) != decoded['archived_projection']:
        raise ValueError('archived projection changed')
    graphs = {'original': raw_graph(left), 's275_archive': raw_graph(right)}
    pairs = decoded['node_pairs']
    mapping = {p['archived']: p['original'] for p in pairs}
    if len(mapping) != len(pairs) or len(set(mapping.values())) != len(pairs):
        raise ValueError('non-bijective correspondence')
    rewrites = [r for r in decoded['archived_projection']['rewrites']
                if r['kind'] == 'conditional_initializer_erasure']
    if [r['role'] for r in rewrites] != list(ROLES):
        raise ValueError('initializer roles changed')
    rows = []
    for rewrite in rewrites:
        role = rewrite['role']
        initializer = rewrite['nodes'][1]
        reads = {side: reaching_reads(graph, role) for side, graph in graphs.items()}
        # A read absent from traversal must remain visible, rather than silently passing.
        for side, graph in graphs.items():
            all_reads = [n['id'] for n in graph
                         if n['op'] == 'Push' and n['operand'] == ['register', role]]
            if all_reads != [r['read'] for r in reads[side]]:
                raise ValueError('unreachable explicit read')
        original = {r['read']: r for r in reads['original']}
        comparisons = []
        for read in reads['s275_archive']:
            target = mapping[read['read']]
            mapped = sorted(-1 if d == -1 else mapping.get(d, -2) for d in read['definitions'])
            comparisons.append({'archived_read': read['read'], 'original_read': target,
                                'mapped_definitions': mapped,
                                'equal': mapped == original[target]['definitions']})
        if sorted(mapping[r['read']] for r in reads['s275_archive']) != sorted(original):
            raise ValueError('incomplete read correspondence')
        rows.append({'role': role,
                     'registers': {side: next(int(k) for k, v in decoded['register_roles'][side].items() if v == role)
                                   for side in graphs},
                     'added_initializer': initializer,
                     'added_initializer_offset': right[initializer]['offset'],
                     'reads': reads, 'correspondence': comparisons,
                     'initializer_reaches_read': any(initializer in r['definitions'] for r in reads['s275_archive']),
                     'entry_reaches_read': any(-1 in r['definitions'] for rs in reads.values() for r in rs)})
    return {'graphs': graphs, 'rows': rows,
            'static_overwrite_property': all(not r['initializer_reaches_read'] and not r['entry_reaches_read'] for r in rows),
            'explicit_definition_correspondence': all(c['equal'] for r in rows for c in r['correspondence']),
            'activation_headers': locked['activation_headers'],
            'limit': 'Explicit StoreRegister/Push-register paths only. Calls are opaque nodes; no stack, hidden activation access, exceptions, reentrancy, scope, arguments, scheduling or native execution model.',
            'coordinates': 'Expanded decoded node IDs and uncompressed SWF offsets, never native PCs or execution order.'}


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    verify_pins(HERE / 'ranking-basis-sha256.json')
    historical = load_prior().diagnose()
    locked = json.loads((HERE.parent / 's302/diagnosis.json').read_text())
    # JSON round-trip canonicalizes integer object keys only; arrays/values are untouched.
    if json.loads(json.dumps(historical)) != locked:
        raise ValueError('locked s302 diagnosis changed')
    return {'slice': 's309', 'base': BASE, 'scope': 'AFTER-s308 rank #1 only: Yulong getHitObj added initializers',
            'production_admitted': False, 'native_parity_proven': False, 'm0_02_status': 'pending',
            'locked_s302_reproduced': True, 'retained_events': locked['retained_events'],
            'audit': audit(locked), 'activation_preservation_proved': False,
            'observer_qualified': False, 'nested_entry_proved': False,
            'direct_removal_dispatch_proved': False,
            'observations': locked['observations'], 'new_builds': 0,
            'new_player_launches': 0, 'new_captures': 0, 'other_ranks_executed': [],
            'product_obligations_closed': 0,
            'blocker': 'Explicit overwrite does not prove activation-visible erasure. Header/register/scope/arguments binding, helper effects and independent observer-off/on controls remain absent; direct removal and natural nested entry are unobserved.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    gates = {'activation-preservation': ('activation_preservation_proved', 'S309_ACTIVATION_PRESERVATION_UNPROVED'),
             'observer': ('observer_qualified', 'S309_OBSERVER_UNPROVED'),
             'nested-entry': ('nested_entry_proved', 'S309_NESTED_ENTRY_UNPROVED'),
             'parent-removal': ('direct_removal_dispatch_proved', 'S309_REMOVAL_DISPATCH_UNPROVED')}
    for flag in gates:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    failures = [code for flag, (field, code) in gates.items()
                if getattr(args, 'require_' + flag.replace('-', '_')) and not result[field]]
    if failures:
        print('; '.join(failures) + ': ' + result['blocker'])
        return 1
    print('S309_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Audit explicit reaching definitions only; never infer live AVM preservation."""
import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '7b214c7f333c4dd33f39cfb7e27b1251e37ab981'
REQUIREMENTS = {
    'activation-preservation': 'S300_ACTIVATION_PRESERVATION_UNPROVED',
    'observer': 'S300_OBSERVER_UNPROVED',
    'external-callsite': 'S300_EXTERNAL_CALLSITE_UNPROVED',
}


def load_module(path):
    spec = importlib.util.spec_from_file_location('s300_locked_' + path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, expected in json.loads(path.read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Locked input hash mismatch: ' + name)


def reaching_reads(graph, register):
    """Finite graph product: (node, most recent explicit store), entry is -1.

    Calls are ordinary archived CFG nodes here. No claim about their dynamic
    effects, exceptions, activation access or additional native edges is made.
    """
    nodes = graph['nodes']
    if not nodes:
        raise ValueError('Empty graph')
    for index, node in enumerate(nodes):
        if node['index'] != index:
            raise ValueError('Noncontiguous graph indices')
        if any(type(j) is not int or not 0 <= j <= len(nodes) for j in node['successors']):
            raise ValueError('Invalid graph edge')
    start = (0, -1)
    parent = {start: None}
    queue = deque([start])
    reads = {}
    while queue:
        state = queue.popleft()
        index, definition = state
        if index == len(nodes):
            continue
        node = nodes[index]
        if node['instruction'] == f'Push register{register}':
            reads.setdefault(index, {})[definition] = state
        outgoing = index if node['instruction'] == f'StoreRegister {register}' else definition
        for successor in node['successors']:
            next_state = (successor, outgoing)
            if next_state not in parent:
                parent[next_state] = state
                queue.append(next_state)

    def witness(state):
        path = []
        while state is not None:
            path.append(state[0])
            state = parent[state]
        return list(reversed(path))

    return [
        {'read_index': index, 'reaching_definitions': sorted(definitions),
         'witness_paths': [{'definition_index': definition, 'node_indices': witness(state)}
                           for definition, state in sorted(definitions.items())]}
        for index, definitions in sorted(reads.items())
    ]


def audit(original, candidate, structural):
    # Recompute the entire locked structural projection before trusting its map.
    recomputed = load_module(HERE.parent / 's291/diagnose.py').audit(original, candidate)
    if json.loads(json.dumps(recomputed)) != structural:
        raise ValueError('Structural correspondence changed')
    correspondence = {r['candidate_index']: r['original_index']
                      for r in structural['node_correspondence']}
    register_map = {int(k): v for k, v in structural['candidate_to_original_register_map'].items()}
    rows = []
    for register in (7, 8, 9, 12):
        envelopes = [e for e in structural['candidate_erasure']
                     if e['reason'] == f'candidate local initialization register{register}; conditional deletion']
        if len(envelopes) != 1:
            raise ValueError('Missing initialization envelope')
        envelope = envelopes[0]
        initialization = envelope['indices'][1]
        candidate_reads = reaching_reads(candidate, register)
        original_reads = reaching_reads(original, register_map[register])
        originals = {r['read_index']: r for r in original_reads}
        matches = []
        for read in candidate_reads:
            original_index = correspondence[read['read_index']]
            mapped = sorted(correspondence[d] if d >= 0 and d != initialization else d
                            for d in read['reaching_definitions'])
            expected = originals[original_index]['reaching_definitions']
            matches.append({'candidate_read_index': read['read_index'],
                            'original_read_index': original_index,
                            'mapped_reaching_definitions': mapped,
                            'original_reaching_definitions': expected,
                            'equal': mapped == expected})
        if {r['original_read_index'] for r in matches} != set(originals):
            raise ValueError('Incomplete read correspondence')
        rows.append({
            'candidate_register': register, 'original_register': register_map[register],
            'initialization_envelope': envelope,
            'candidate_reads': candidate_reads, 'original_reads': original_reads,
            'read_correspondence': matches,
            'initialization_reaches_explicit_read': any(initialization in r['reaching_definitions'] for r in candidate_reads),
            'entry_value_reaches_explicit_read': any(-1 in r['reaching_definitions'] for r in candidate_reads),
            'all_explicit_read_definitions_correspond': all(r['equal'] for r in matches),
        })
    return {
        'method': 'Reachable (node, last explicit StoreRegister) graph product; -1 denotes entry value; both branch successors included; no path-feasibility pruning.',
        'domain': 'Archived explicit intrafunction CFG only; calls, exceptions, reentrancy and activation observability remain outside this static result.',
        'rows': rows,
        'static_overwrite_property': all(not r['initialization_reaches_explicit_read']
                                         and not r['entry_value_reaches_explicit_read']
                                         and r['all_explicit_read_definitions_correspond'] for r in rows),
        'headers_preserved_verbatim': {k: structural[k] for k in ('original_header', 'candidate_header')},
        'remaining_obligations': [
            'Live activation/preload and scope binding correspondence.',
            'Helper identity and absence of mutation, exceptions, reentrancy, lifetime and scheduling effects.',
            'Initialization erasure preserves activation-visible behavior beyond explicit register reads.',
            'Double-Not erasure preserves coercion on actual values.',
            'Independent observer-off/on controls and natural executed/skipped callsite observations.',
        ],
    }


def diagnose():
    verify_pins(HERE / 'ranking-basis-sha256.json')
    verify_pins(HERE / 'input-sha256.json')
    prior = load_module(HERE.parent / 's291/diagnose.py').diagnose()
    retained = json.loads((HERE.parent / 's291/diagnosis.json').read_text())
    # JSON canonicalization accounts only for the old integer register-map keys.
    if json.loads(json.dumps(prior)) != retained:
        raise ValueError('Locked s291 replay differs')
    graphs = json.loads((HERE.parent / 's283/diagnosis.json').read_text())
    result = audit(graphs['original_projection'], graphs['candidate_projection'], retained['audit'])
    return {
        'slice': 's300', 'base': BASE, 'scope': 'AFTER-s299 rank 1 only',
        'production_admitted': False, 'native_parity_proven': False,
        'activation_preservation_proved': False, 'observer_qualified': False,
        'external_callsite_execution_proved': False,
        'historical_execution_observed': prior['historical_execution_observed'],
        'historical_events_revalidated': prior['historical_events_revalidated'],
        'locked_s291_reproduced': True, 'audit': result,
        'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0,
        'product_obligations_closed': 0,
        'blocker': 'Explicit CFG overwrite is not activation-visible erasure, helper non-perturbation or live callsite evidence.',
        'next_discriminator': 'Qualify header/preload/scope binding and activation-visible erasure against the pinned compiled function before helper installation or natural paired controls.',
        'requirement_failure_codes': REQUIREMENTS,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    for name in REQUIREMENTS:
        parser.add_argument('--require-' + name, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, 'S300_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [code for name, code in REQUIREMENTS.items()
                if getattr(args, 'require_' + name.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + ': ' + report['blocker'] + '\n')
    print('S300_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()

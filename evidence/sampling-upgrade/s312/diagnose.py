"""Qualify archived body-push binding boundaries; never admit a live observer."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '19aef574dbba5e574ffa492eabb6066dd6214f64'
FLAGS = ('preloadParentFlag', 'preloadRootFlag', 'suppressSuperFlag',
         'preloadSuperFlag', 'suppressArgumentsFlag', 'preloadArgumentsFlag',
         'suppressThisFlag', 'preloadThisFlag', 'preloadGlobalFlag')
GATES = {name: 'S312_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('scope-binding', 'activation-erasure', 'helper-effects',
                      'off-on', 'external-callsite')}


def load(slice_name):
    spec = importlib.util.spec_from_file_location('s312_' + slice_name,
                                                HERE.parent / slice_name / 'diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + name)


def decode_header(header, source):
    """Interpret exporter syntax, not native activation semantics."""
    asm = source.split('public String getASMSource(', 1)[1].split('\n    }', 1)[0]
    if re.findall(r'\+ ", " \+ (\w+Flag)', asm) != list(FLAGS):
        raise ValueError('Exporter flag order changed')
    reg_source = source.split('public HashMap<Integer, String> getRegNames()', 1)[1]
    preload_order = re.findall(r'if \((\w+Flag)\) \{\s+funcRegNames.put\(pos, "([^"]+)"\);\s+pos\+\+;', reg_source)
    if preload_order != [('preloadThisFlag', 'this'), ('preloadArgumentsFlag', 'arguments'),
                         ('preloadSuperFlag', 'super'), ('preloadRootFlag', '_root'),
                         ('preloadParentFlag', '_parent'), ('preloadGlobalFlag', '_global')]:
        raise ValueError('Exporter preload naming changed')
    match = re.fullmatch(r'DefineFunction2 "on_enterframe", 0, (\d+), ((?:(?:true|false), ){8}(?:true|false)) \{', header)
    if not match:
        raise ValueError('Unsupported callback header')
    flags = dict(zip(FLAGS, (s == 'true' for s in match[2].split(', '))))
    names = [name for flag, name in preload_order if flags[flag]]
    return {'raw': header, 'register_count': int(match[1]), 'flags': flags,
            'exporter_preload_names': {str(i): name for i, name in enumerate(names, 1)}}


def audit(original, candidate, structural, source):
    # Validate the full unprojected bodies before using the old correspondence.
    if json.loads(json.dumps(load('s291').audit(original, candidate))) != structural:
        raise ValueError('Full callback correspondence changed')
    headers = {side: decode_header(graph['header'], source)
               for side, graph in (('original', original), ('candidate', candidate))}
    mapping = structural['candidate_to_original_register_map']
    preload_pairs = []
    for reg, name in headers['original']['exporter_preload_names'].items():
        candidates = [r for r, n in headers['candidate']['exporter_preload_names'].items() if n == name]
        if len(candidates) != 1 or mapping[candidates[0]] != int(reg):
            raise ValueError('Preload name correspondence differs')
        preload_pairs.append({'name': name, 'original_register': int(reg),
                              'candidate_register': int(candidates[0]), 'live_identity': None})
    inventories = {}
    for side, graph in (('original', original), ('candidate', candidate)):
        nodes = graph['nodes']
        inventories[side] = {
            'node_count': len(nodes),
            'scope_operations': [n for n in nodes if n['instruction'] in
                                 ('GetVariable', 'SetVariable', 'DefineLocal', 'DefineLocal2', 'With', 'GetMember', 'SetMember', 'Delete', 'Delete2', 'Enumerate', 'Enumerate2')],
            'calls': [{'node': n, 'preceding_nodes': nodes[max(0,n['index']-4):n['index']]}
                      for n in nodes if n['instruction'] in ('CallMethod', 'CallFunction', 'NewMethod', 'NewObject')],
            'returns': [n for n in nodes if n['instruction'] == 'Return'],
        }
    nodes = candidate['nodes']
    owner_uses = [n for n in nodes if n['instruction'] in ('Push register1', 'StoreRegister 1')]
    helpers = [e for e in structural['candidate_erasure'] if e['reason'].startswith('hypothetical pass-through:')]
    initializations = [e for e in structural['candidate_erasure'] if e['reason'].startswith('candidate local initialization')]
    return {
        'coordinate_kind': 'Expanded archived pcode node indices, not byte offsets or executed order',
        'headers': headers,
        'changed_header_fields': ['register_count'] + [flag for flag in FLAGS if headers['original']['flags'][flag] != headers['candidate']['flags'][flag]],
        'preload_name_correspondence': preload_pairs,
        'candidate_added_this_uses': owner_uses,
        'full_callback_inventory': inventories,
        'helper_envelopes': helpers,
        'initialization_envelopes': initializations,
        'scope_operation_correspondence': [r for r in structural['node_correspondence'] if r['instruction'] in ('GetVariable', 'SetVariable')],
        'initialization_cut_context': [
            {'store_index': e['indices'][1],
             'helper_calls_at_lower_node_indices': [h['indices'][-1] for h in helpers if h['indices'][-1] < e['indices'][1]],
             'helper_calls_at_higher_node_indices': [h['indices'][-1] for h in helpers if h['indices'][-1] > e['indices'][1]],
             'live_activation_visibility': None} for e in initializations],
        'static_preload_name_correspondence_proved': True,
        'live_scope_identity': None, 'activation_visible_erasure': None,
        'helper_effect_observation': None, 'independent_off_on_observation': None,
        'limit': 'Exporter names and explicit scope-operation correspondence do not establish live bindings. Lower/higher indices are lexical positions, not executed paths. No claim excludes hidden activation access, exceptions, reentrancy, lifetime or scheduling effects. Double-Not coercion remains unproved.'}


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    prior = load('s300').diagnose()
    if prior != json.loads((HERE.parent / 's300/diagnosis.json').read_text()):
        raise ValueError('Locked s300 replay changed')
    graphs = json.loads((HERE.parent / 's283/diagnosis.json').read_text())
    structural = json.loads((HERE.parent / 's291/diagnosis.json').read_text())['audit']
    return {
        'slice': 's312', 'base': BASE, 'scope': 'AFTER-s308 rank #4 only',
        'production_admitted': False, 'native_parity_proven': False,
        'm0_02_status': 'pending', 'product_obligations_closed': 0,
        'locked_s300_reproduced': True,
        'retained_static_overwrite_property': prior['audit']['static_overwrite_property'],
        'historical_events_revalidated': prior['historical_events_revalidated'],
        'historical_execution_observed': prior['historical_execution_observed'],
        'binding_audit': audit(graphs['original_projection'], graphs['candidate_projection'], structural,
                               (HERE / 'ActionDefineFunction2.java').read_text()),
        'gates': {name: {'proved': False, 'code': code} for name, code in GATES.items()},
        'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0,
        'other_ranks_executed': [],
        'exclusions': ['repeat solved dataflow as new work', 'early initialization', 'receiver exemption',
                       'extra hitTest', 'tick41', 'runtime changes', 's254-s311 edits',
                       'game/scripts/contracts/shared sampler/threshold/validator changes'],
        'blocker': 'Static preload names correspond, but changed this suppression/preload and defining scope lack live binding evidence. Initialization erasure remains activation-visible-unproved. Independent helper effects and off/on controls are blocked on that qualification.',
        'next_discriminator': 'Establish original/candidate defining scope and this/root/parent identities for a retained invocation, including suppression and hidden activation visibility; qualify initialization and double-Not erasure. Only then independently measure helper effects and natural executed/skipped observer-off/on controls. No helper installation or capture is admitted here.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError, IndexError) as exc:
        parser.exit(1, 'S312_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S312_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

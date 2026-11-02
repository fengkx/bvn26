"""Audit locked AImain evidence and native resolver prerequisites; never infer identity."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '0038929ce894539da159afe3331ba0a3e8e2da25'
QUERIES = {'slot-type': 'image lookup -t DisplayObjectContainer', 'reference-type': 'image lookup -t MovieClipObject', 'slot-reference-symbols': 'image lookup -r -n "(GetInstanceAtDepth|GetChildAtDepth|ResolveMovieClip|MovieClipReference)" "Flash Player Debugger"', 'pool-lifetime-symbols': 'image lookup -r -n "(AllocMovieClip|FreeMovieClip|DisplayObjectPool|DestroyMovieClip)" "Flash Player Debugger"'}
EXCLUSIONS = [
    'pointer-only identity', '0->1 alias', 'token-loss identity',
    'unloaded exemption', 'import inventory as runtime proof',
    'property deletion as content clearing', 'ranks 1-7 and 9',
]
REQUIREMENTS = {
    'slot-reference': 'S298_SLOT_REFERENCE_UNPROVED',
    'content-clearing': 'S298_CONTENT_CLEARING_UNPROVED',
    'replacement': 'S298_REPLACEMENT_UNPROVED',
    'allocation-identity': 'S298_POOL_GENERATIONS_UNPROVED',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit_facility(record, binary_sha256, read_text):
    if record['binary_sha256'] != binary_sha256:
        raise ValueError('different player executable')
    if any(record[key] != 0 for key in ('player_launches', 'process_attaches', 'new_captures')) or record['live_lifetime_events'] is not None:
        raise ValueError('execution evidence requires independent analysis')
    if [row['name'] for row in record['checks']] != list(QUERIES):
        raise ValueError('missing or duplicated resolver query')
    for row in record['checks']:
        query = QUERIES[row['name']]
        expected = ['lldb', '--batch', '-o', 'settings set target.preload-symbols false',
                    '-o', f'target create --no-dependents "{record["binary"]}"', '-o', query]
        transcript = read_text(row['log'])
        if row['command'] != expected or row['exit'] != 1:
            raise ValueError('changed resolver outcome requires independent analysis')
        if sha(transcript.encode()) != row['sha256']:
            raise ValueError('changed facility transcript')
        # An empty lookup result differs from failure to create the target.
        suffix = '(lldb) ' + query + '\n'
        if "Current executable set to '" + record['binary'] + "' (x86_64)." not in transcript or not transcript.endswith(suffix):
            raise ValueError('lookup did not reach the expected empty result')
        cost = row['elapsed_seconds']
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not 0 < cost < float('inf'):
            raise ValueError('invalid measured cost')
    return {'query_count': len(QUERIES), 'matching_layouts_or_symbols_observed': 0,
            'native_slot_reference_resolver_qualified': False,
            'limitation': 'Candidate names are search hypotheses, not established native class names. Empty lookup results do not prove that these objects are absent or native analysis is impossible.'}


def control_obligations(prior):
    # These are missing observations, not invented native behavior or test fixtures.
    return {
        'retained_content_clear': {
            'historical_signal': prior['controls']['retained_content_clear'],
            'qualified': False,
            'required_order': [
                'Resolve slot and saved referent independently before clearing.',
                'Observe an actual content-clear operation and complete pool lifetime coverage.',
                'Resolve both again; establish retention independently of address or token equality.',
            ],
            'observed_native_generations': None,
        },
        'same_name_depth_replacement': {
            'historical_signal': prior['controls']['same_name_same_depth_replacement'],
            'qualified': False,
            'required_order': [
                'Resolve the original slot and saved referent with a live generation.',
                'Observe removal, destruction/free and pool lifecycle events in actual execution order.',
                'Observe replacement creation and resolve slot and saved referent independently.',
            ],
            'observed_native_generations': None,
        },
        'free_reuse': {
            'qualified': False,
            'required_order': [
                'Start complete object/pool lifetime coverage before control allocation.',
                'Observe the old generation ending before actual address reuse begins a new generation.',
                'Resolve slot and saved referent after reuse without assigning identity by pointer.',
            ],
            'observed_native_generations': None,
            'limitation': 'Removal need not imply immediate free. Unexercised reuse or a coverage gap remains unproved; generic malloc/free hooks alone do not cover internal pools.',
        },
    }


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    spec = importlib.util.spec_from_file_location('s289_locked', HERE.parent / 's289/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.diagnose()
    if replay != json.loads((HERE.parent / 's289/diagnosis.json').read_text()):
        raise ValueError('locked s289 diagnosis mismatch')
    pinned_player = json.loads((HERE.parent / 's279/diagnosis.json').read_text())['facility']['binary_sha256']
    facility = json.loads((HERE / 'facility.json').read_text())
    resolution = audit_facility(facility, pinned_player, lambda path: (HERE / path).read_text())
    return {
        'base': BASE, 'scope': 's298 / AFTER-s290 rank #8 only',
        'status': 'honest_unproved',
        'production_admitted': False, 'native_parity_proven': False,
        'slot_reference_proved': False, 'allocation_identity_proved': False,
        'product_obligations_closed': 0, 'locked_s289_reproduced': True,
        'retained_capture': replay['retained_capture'],
        'source_bindings': replay['source_bindings'],
        'reference_window': replay['reference_window'],
        'target_sites': replay['target_sites'],
        'native_observations': replay['native_observations'],
        'control_obligations': control_obligations(replay),
        'facility': facility, 'resolver_audit': resolution,
        'new_builds': 0, 'new_captures': 0, 'new_player_launches': 0,
        'actual_native_controls_executed': False,
        'absence_of_possible_resolver_proved': False,
        'exclusions_enforced': EXCLUSIONS,
        'requirement_failure_codes': REQUIREMENTS,
        'blocker': 'No native parent/depth slot or saved-reference resolver/layout qualified. No actual retained-content clearing, replacement or free/reuse control has a complete pool-aware ordered generation ledger.',
        'next_discriminator': replay['next_discriminator'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for name in REQUIREMENTS:
        parser.add_argument('--require-' + name, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, 'S298_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = [code + ': ' + report['blocker'] for name, code in REQUIREMENTS.items()
                if getattr(args, 'require_' + name.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + '\n')
    print('S298_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()

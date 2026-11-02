"""Audit the locked P1 loader evidence and bounded native resolver attempts."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
QUERIES = {
    'loader-type': 'image lookup -t MovieClipLoader',
    'request-type': 'image lookup -t URLRequest',
    'stream-type': 'image lookup -t CFReadStreamRef',
    'request-consumer-symbols': 'image lookup -r -n "(ReadStream|LoadRequest|LoadContext|LoaderInfo|StreamConsumer)" "Flash Player Debugger"',
}
EXCLUSIONS = [
    'static hash/live-byte substitution', 'mutable request proxy', 'helper stamp',
    'global counter', 'receipt resealing', 'rollout', 'other ranks',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit_facility(record, binary_sha256, read_text):
    if record['binary_sha256'] != binary_sha256:
        raise ValueError('different player executable')
    if any(record[key] != 0 for key in ('player_launches', 'process_attaches', 'new_captures')) or record['live_read_events'] is not None:
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
            'native_request_resolver_qualified': False,
            'limitation': 'Candidate names are search hypotheses, not established native class names. Empty lookup results do not prove that these objects are absent or native analysis is impossible.'}


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    spec = importlib.util.spec_from_file_location('s287_locked', HERE.parent / 's287/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.diagnose()
    if replay != json.loads((HERE.parent / 's287/diagnosis.json').read_text()):
        raise ValueError('locked s287 diagnosis mismatch')
    facility = json.loads((HERE / 'facility.json').read_text())
    resolution = audit_facility(facility, replay['facility']['binary_sha256'],
                                lambda path: (HERE / path).read_text())
    return {
        'base': '9ee71eaf6b73fffbe7277cf4d79fc4a412dab76d',
        'scope': 'AFTER-s290 rank #7 only; s259-normal P1',
        'production_admitted': False, 'native_parity_proven': False,
        'loader_attestation_proved': False, 'normal_association_qualified': False,
        'pre_advance_target_proved': False, 'wrong_resource_control_qualified': False,
        'wrong_resource_control_executed': False, 'product_obligations_closed': 0,
        'locked_s287_reproduced': True,
        'historical_normal': replay['historical_normal'],
        'source_loader_order': replay['source_loader_order'],
        'static_read_stubs': replay['static_read_stubs'],
        'facility': facility, 'resolver_audit': resolution,
        'observations': dict(replay['observations']),
        'new_builds': 0, 'new_captures': 0, 'new_player_launches': 0,
        'exclusions_enforced': EXCLUSIONS,
        'blocker': 'No executed P1 read-return/buffer-to-consumer-to-immutable-request resolver or target observation before inline loadStep advance. Static stubs and empty candidate lookups cannot qualify that join.',
        'wrong_resource_blocker': 'Normal association must be independently qualified first; actual Yihu-for-Yijiao control not executed.',
        'next_discriminator': 'Resolve the actual P1 consuming native call chain and immutable request identity, retain returned byte ranges (or mapped ranges actually consumed), and observe its callback target before loadStep++. Qualify observer preservation and same-request init/use/replacement separately. Only then run an isolated wrong-resource control with expected Yijiao identity unchanged.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-loader-attestation', action='store_true')
    parser.add_argument('--require-pre-advance-target', action='store_true')
    parser.add_argument('--require-wrong-resource-control', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = []
    if args.require_loader_attestation:
        failures.append('S297_LOADER_ASSOCIATION_UNPROVED: ' + report['blocker'])
    if args.require_pre_advance_target:
        failures.append('S297_PRE_ADVANCE_TARGET_UNPROVED: callback target and immutable request unobserved')
    if args.require_wrong_resource_control:
        failures.append('S297_WRONG_RESOURCE_BLOCKED: ' + report['wrong_resource_blocker'])
    if failures:
        parser.exit(1, '\n'.join(failures) + '\n')
    print('S297_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()

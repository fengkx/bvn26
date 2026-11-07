"""Replay locked ones evidence and report the failed native entry derivation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '8e873eaffaac7cf80c0a3f90a32ef1a6c032ab2f'
GATES = {
    'target-entry': 'S337_BYTE_BOUND_TARGET_ENTRY_UNPROVED',
    'outer-lifetime': 'S337_INDEPENDENT_OUTER_LIFETIME_UNPROVED',
    'independent-controls': 'S337_INDEPENDENT_CONTROLS_UNPROVED',
    'child-clock': 'S337_CHILD_CLOCK_UNPROVED',
    'fresh-capture': 'S337_FRESH_CAPTURE_BLOCKED',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_pins(path):
    for name, expected in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + name)


def load_prior():
    spec = importlib.util.spec_from_file_location('s337_locked_s328', HERE.parent / 's328/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    return prior


def replay():
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's328/diagnosis.json').read_text()):
        raise ValueError('complete locked s328 diagnosis changed')
    return prior


def audit_search(record):
    if sha((json.dumps(record, indent=2) + '\n').encode()) != SEARCH_SHA256:
        raise ValueError('native search changed; independent review required')
    return record


SEARCH_SHA256 = '80039e032e07609212832205df6bec5afd6ecb3c583b81b8d916b2e60eb16768'


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    prior = replay()
    search = audit_search(json.loads((HERE / 'native-search.json').read_text()))
    return {
        'slice': 's337', 'base': BASE, 'scope': 'AFTER-s335 rank #2 only',
        'authority': 'evidence/sampling-upgrade/next-fix-priority-after-s335.md',
        'production_admitted': False, 'native_parity_proven': False, 'm0_02_status': 'pending',
        'locked_s328_reproduced': True,
        'historical_validation_only': prior['historical_validation_only'],
        'native_derivation_attempt': search,
        'new_mechanism_proof': False, 'independent_observations_new': [],
        'live_entry_resolver': None, 'live_instance_resolver': None,
        'qualification_matrix': prior['qualification_matrix'],
        'controls': {name: {'executed': False, 'qualified': None,
                          'blocker': 'No byte-bound entry and independent outer lifetime channel.'}
                     for name in ('isolated_repeated_target', 'isolated_changed_target',
                                  'same_depth_replacement', 'observer_off_on')},
        'observer_qualified': False, 'independent_controls_proved': False,
        'independent_child_clock_proved': False, 'fresh_capture_eligible': False,
        'new_builds': 0, 'new_player_launches': 0, 'new_attaches': 0,
        'new_memory_reads': 0, 'new_captures': 0, 'new_images': 0,
        'other_ranks_executed': [], 're_ranked': False, 'product_obligations_closed': 0,
        'blocker': 'The exact NUL-delimited native name anchor was absent in the locked disk binary. This bounded route derived no executable target-entry site or independent outer-instance lifetime channel. It does not rule out other representations or channels. Controls and fresh capture remain blocked before execution.',
        'next_required_observation': 'Independently derive and byte-bind actual entry dispatch for all ten frames and outer-instance lifetime; bind loaded module/run and uninterrupted instance generations. Qualify isolated repeated/changed/replacement/off-on controls with selection, entry and following root/callback order before fresh ones capture.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [code for flag, code in GATES.items()
                if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + report['blocker'])
        return 1
    print('S337_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

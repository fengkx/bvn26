"""Audit the independent s352 UI route without promoting facility output to dispatch."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def audit_attempts(record):
    for key in ('window_state_obtained', 'input_control_established', 'native_receipt'):
        if record[key] is not False:
            raise ValueError('changed UI evidence requires independent analysis')
    if any(record[key] != 0 for key in ('ui_inputs_sent', 'instrumented_movie_launches', 'new_capture_count')):
        raise ValueError('execution evidence requires independent analysis')
    if record['app_activation_unknown'] is not True or record['no_dispatch_observed'] is not None:
        raise ValueError('facility result is not activation or no-dispatch proof')
    if record['original_launch_requests'] != 1:
        raise ValueError('retain the original launch request')
    bundle = json.loads((HERE / 'bundle-window-result.json').read_text())
    if bundle['stdout'] != 'matching_processes=2\npid=50810;frontmost=false\npid=50810;frontmost=false\n\n' or bundle['exit_code'] != 0:
        raise ValueError('bundle query changed; reassess window binding')
    return sum(json.loads((HERE / name).read_text()).get('wall_seconds', 0)
               for name in record['raw_records']) + sum(
        row['reported_wall_seconds'] for row in json.loads((HERE / 'cua-attempts.json').read_text())['attempts'])


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input changed: ' + path)
    record = json.loads((HERE / 'ui-control-attempts.json').read_text())
    cost = audit_attempts(record)
    spec = importlib.util.spec_from_file_location('s342_locked', HERE.parent / 's342/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.diagnose()
    if replay != json.loads((HERE.parent / 's342/diagnosis.json').read_text()):
        raise ValueError('locked s342 diagnosis mismatch')
    return {
        'base': '26cbf097980e84682d89ef48daf81ca4876a6643', 'scope': 'AFTER-s344 rank #8 only',
        'production_admitted': False, 'native_parity_proven': False,
        'thin_coverage_cut_proved': False, 'product_obligations_closed': 0,
        'constraints': {
            'allowed_rank': 8, 'other_ranks_executed': False,
            'forced_frames': False, 'as_calls_as_input': False,
            'listener_order_assumed': False, 'combat_tape_changes': False,
            'runtime_changes': False, 'prior_slice_changes': False,
        },
        'native_ui_control_established': False,
        'facility_reported_wall_seconds': cost,
        'ui_case_executed': False, 'new_captures': 0,
        'candidate_compiled': False, 'candidate_opcode_preservation_checked': False,
        'candidate_native_behavior_preservation_proved': False,
        'observations': {key: None for key in (
            'frame10', 'enter_dispatch', 'release_dispatch', 'handler_entry',
            'no_dispatch_controls', 'listener_order', 'handler_return')},
        'candidate_patch_sha256': replay['candidate_patch_sha256'],
        'family_obligations': replay['family_obligations'],
        'historical_s263_replay': replay['historical_s263_replay'],
        'locked_s342_diagnosis': replay,
        'blocker': record,
        'deferred_steps': ['Compile isolated candidate and check complete original opcode/control-flow projection',
                           'Qualify independent live placement and observer perturbation',
                           'Execute original-menu Enter/release and no-dispatch controls'],
        'next_discriminator': 'Disambiguate the receipt-pinned running player and obtain actual window/input binding. Process rows, launch acceptance and inventory are insufficient. Then qualify the isolated build before original-menu execution; no forced frames, AS input calls, assumed listener order or return/full-AS claim.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-native-ui', action='store_true')
    parser.add_argument('--require-thin-coverage', action='store_true')
    parser.add_argument('--require-full-as', action='store_true')
    parser.add_argument('--require-opcode-qualification', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.require_full_as:
        parser.exit(1, 'S352_FULL_AS_UNPROVED: ' + report['historical_s263_replay']['strict_full_as_error'] + '\n')
    if args.require_native_ui:
        parser.exit(1, 'S352_NATIVE_UI_UNPROVED: no target window/input binding; process rows and bundle ambiguity are not control\n')
    if args.require_opcode_qualification:
        parser.exit(1, 'S352_OPCODE_QUALIFICATION_UNPROVED: compilation deferred behind native UI prerequisite\n')
    if args.require_thin_coverage:
        parser.exit(1, 'S352_BUTTON_ENTRY_UNPROVED: Enter/release and no-dispatch controls unobserved\n')
    print('s352 diagnosis verified; native UI prerequisite blocked, entry unproved')


if __name__ == '__main__':
    main()

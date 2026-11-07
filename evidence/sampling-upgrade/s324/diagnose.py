"""Revalidate Button2009 preparation and the failed native UI prerequisite."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def audit_attempts(record):
    attempts = record['attempts']
    if len(attempts) != 1 or any(row['window_state_obtained'] is not False for row in attempts):
        raise ValueError('changed UI evidence requires independent analysis')
    if any(record[key] != 0 for key in ('ui_inputs_sent', 'instrumented_movie_launches', 'new_capture_count')):
        raise ValueError('execution evidence requires independent analysis')
    if record['native_receipt'] is not False or record['app_activation_unknown'] is not True:
        raise ValueError('facility output is not a native receipt or activation proof')
    if attempts[-1]['result'] != 'Computer Use server error -10005: timeoutReached':
        raise ValueError('missing retained native window failure')
    if record['facility'] != 'mcp__cua_repl.js' or attempts[0]['operation'] != 'let app = await cua.getApp("/Users/fengkx/me/code/flash-player/Flash Player.app");':
        raise ValueError('exact installed path operation required')
    cost = attempts[0]['reported_wall_seconds']
    if not isinstance(cost, (int, float)) or not 0 < cost < float('inf'):
        raise ValueError('invalid measured facility cost')
    return cost


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input changed: ' + path)
    record = json.loads((HERE / 'ui-control-attempts.json').read_text())
    cost = audit_attempts(record)
    spec = importlib.util.spec_from_file_location('s315_locked', HERE.parent / 's315/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.diagnose()
    if replay != json.loads((HERE.parent / 's315/diagnosis.json').read_text()):
        raise ValueError('locked s315 diagnosis mismatch')
    return {
        'base': '32dec0541e1586c5ae9790f06ca5613956dc9ed8', 'scope': 'AFTER-s317 rank #7 only',
        'production_admitted': False, 'native_parity_proven': False,
        'thin_coverage_cut_proved': False, 'product_obligations_closed': 0,
        'constraints': {
            'allowed_rank': 7, 'other_ranks_executed': False,
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
        'locked_s315_diagnosis': replay,
        'blocker': record,
        'deferred_steps': ['Compile isolated candidate and check complete original opcode/control-flow projection',
                           'Qualify independent live placement and observer perturbation',
                           'Execute original-menu Enter/release and no-dispatch controls'],
        'next_discriminator': 'Obtain native Flash window state and input control through the exact installed app path. Inventory success is insufficient. Then qualify the isolated build before original-menu execution; no forced frames, AS input calls, assumed listener order or return/full-AS claim.',
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
        parser.exit(1, 'S324_FULL_AS_UNPROVED: ' + report['historical_s263_replay']['strict_full_as_error'] + '\n')
    if args.require_native_ui:
        parser.exit(1, 'S324_NATIVE_UI_UNPROVED: exact-path selection timed out before input\n')
    if args.require_opcode_qualification:
        parser.exit(1, 'S324_OPCODE_QUALIFICATION_UNPROVED: compilation deferred behind native UI prerequisite\n')
    if args.require_thin_coverage:
        parser.exit(1, 'S324_BUTTON_ENTRY_UNPROVED: Enter/release and no-dispatch controls unobserved\n')
    print('s324 diagnosis verified; native UI prerequisite blocked, entry unproved')


if __name__ == '__main__':
    main()

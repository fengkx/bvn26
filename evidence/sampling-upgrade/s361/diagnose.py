"""Audit s361 process/window association without promoting metadata to UI proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('process-window-association', 'native-ui', 'opcode-qualification',
         'thin-coverage', 'full-as')


def associate(record, receipt):
    if record['observed_binary_path'] != receipt['binary'] or record['observed_binary_sha256'] != receipt['binary_sha256']:
        raise ValueError('receipt binary mismatch')
    ps, swift = record['records']
    if ps['exit_code'] != 0 or swift['exit_code'] != 0:
        raise ValueError('facility query failed')
    state = json.loads(swift['stdout'])
    matches = [app for app in state['applications'] if app['executable_url'] == receipt['binary']]
    if len(matches) != 1 or matches[0]['terminated']:
        raise ValueError('running executable association ambiguous')
    app = matches[0]
    process_rows = [line.strip().split(maxsplit=1) for line in ps['stdout'].splitlines() if line.strip()]
    if [str(app['pid']), receipt['binary']] not in process_rows:
        raise ValueError('independent process path does not match')
    if not state['window_query_available']:
        raise ValueError('window query unavailable')
    # Bind the title to the worktree used at observation time, not the recheck host.
    title = '/Users/fengkx/me/agent-code/bvn2_6-next-slice/game/main.swf'
    windows = [w for w in state['player_windows']
               if w['kCGWindowOwnerPID'] == app['pid'] and w.get('kCGWindowName') == title]
    if len(windows) != 1:
        raise ValueError('movie-titled owner record absent or ambiguous')
    return {'pid': app['pid'], 'executable_path': app['executable_url'],
            'binary_sha256': record['observed_binary_sha256'],
            'window_number': windows[0]['kCGWindowNumber'],
            'window_title': title, 'window_bounds': windows[0]['kCGWindowBounds'],
            'application_active_at_query': app['active'],
            'onscreen_key_present': 'kCGWindowIsOnscreen' in windows[0],
            'loaded_image_bytes_proved': False, 'loaded_movie_identity_proved': False,
            'visible_content_proved': False, 'input_target_proved': False}


def audit_claims(record):
    expected = {'running_path_association_observed': True, 'window_owner_record_observed': True,
                'visible_window_proved': False, 'input_control_established': False,
                'native_dispatch_proved': False, 'ui_inputs_sent': 0,
                'original_launch_requests': 0, 'instrumented_movie_launches': 0,
                'new_behavior_captures': 0, 'candidate_compiled': False, 'no_dispatch_observed': None}
    for key, value in expected.items():
        if type(record[key]) is not type(value) or record[key] != value:
            raise ValueError('changed evidence requires independent analysis: ' + key)


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input changed: ' + path)
    record = json.loads((HERE / 'ui-control-attempts.json').read_text())
    audit_claims(record)
    association = associate(json.loads((HERE / 'facility-result.json').read_text()),
                            json.loads((HERE.parent / 's343/lookup-candidates.json').read_text()))
    spec = importlib.util.spec_from_file_location('s352_locked', HERE.parent / 's352/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.diagnose()
    if replay != json.loads((HERE.parent / 's352/diagnosis.json').read_text()):
        raise ValueError('complete locked s352 replay mismatch')
    return {
        'scope': 'AFTER-s353 rank #8 only',
        'production_admitted': False, 'native_parity_proven': False,
        'm0_02_status': 'pending', 'product_obligations_closed': 0,
        'process_window_metadata_association_proved': True,
        'association': association, 'native_ui_control_established': False,
        'candidate_compiled': False, 'candidate_opcode_preservation_checked': False,
        'thin_coverage_cut_proved': False, 'ui_case_executed': False,
        'observations': {key: None for key in ('frame10', 'enter_dispatch', 'release_dispatch',
                         'handler_entry', 'handler_return', 'no_dispatch_controls', 'listener_order')},
        'constraints': {'allowed_rank': 8, 'other_ranks_executed': False,
                        'forced_frames': False, 'as_calls_as_input': False,
                        'listener_order_assumed': False, 'combat_tape_changes': False,
                        'runtime_changes': False, 'prior_slice_changes': False},
        'blocker': record, 'locked_s352_diagnosis': replay,
        'next_discriminator': 'Obtain visible content and an input binding for the receipt-path process, then qualify compiled opcode projection and observer off/on before original-menu Enter/release and observed no-dispatch controls. Owner metadata and timeout prove no dispatch outcome.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-' + gate, action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    failures = [gate for gate in GATES if gate != 'process-window-association'
                and getattr(args, 'require_' + gate.replace('-', '_'))]
    if failures:
        parser.exit(1, 'S361_UNPROVED: ' + ', '.join(failures) + '\n')
    print('S361_AUDIT_OK: metadata association only; production_admitted=false')


if __name__ == '__main__':
    main()

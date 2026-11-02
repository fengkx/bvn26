"""Replay locked Button2009 evidence and reject an unexecuted UI case."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input changed: ' + path)
    prior = load('s271_locked', HERE.parent / 's271/diagnose.py').diagnose()
    case = json.loads((HERE / 'ui-case.json').read_text())
    attempt = json.loads((HERE / 'capture-attempt.json').read_text())
    if case['status'] != 'not_executed' or attempt['ui_inputs_sent'] != 0:
        raise ValueError('capture status changed; independent native analysis required')
    scripts = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']}
    candidate = load('s276_prepare', HERE / 'prepare_probe.py').patches(scripts)
    return {
        'base': '6179ca1e', 'scope': 'AFTER-s272 rank 4 only',
        'production_admitted': False, 'native_parity_proven': False,
        'thin_coverage_cut_proved': False, 'product_obligations_closed': 0,
        'ui_case': case['id'], 'ui_case_executed': False,
        'frame10_observed': None, 'enter_dispatch_observed': None,
        'release_dispatch_observed': None, 'handler_entries_observed': None,
        'no_dispatch_controls_observed': None, 'listener_order_observed': None,
        'handler_return_observed': None,
        'candidate_patch_sha256': {p: hashlib.sha256(s.encode()).hexdigest() for p, s in candidate.items()},
        'candidate_compiled': False, 'candidate_opcode_preservation_checked': False,
        'candidate_native_behavior_preservation_proved': False,
        'locked_replay': {k: prior[k] for k in ('events', 'root_samples', 'unvisited', 'uninstrumented', 'raw_capture_structure_exit', 'strict_full_as_exit', 'strict_full_as_error')},
        'family_obligations': [r['id'] for r in prior['family']],
        'blocker': attempt,
        'next_discriminator': 'Restore native UI control, compile the isolated candidate against original main, and verify original opcode/control-flow projection before capture. Execute ui-case.json via original menus, record actual native input callbacks and exact Button2009 entries separately, bracket live placement with independent timeline/slot observations and no-dispatch intervals. Preserve complete logs and actual listener ordering. Do not promote entry or return coverage from preparation or absent records.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-thin-coverage', action='store_true')
    parser.add_argument('--require-full-as', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.require_full_as:
        parser.exit(1, report['locked_replay']['strict_full_as_error'] + '\n')
    if args.require_thin_coverage:
        parser.exit(1, 'UI case not executed: native dispatch, entry and no-dispatch controls unobserved\n')
    print('s276 diagnosis verified; UI execution blocked, no coverage cut proved')


if __name__ == '__main__':
    main()

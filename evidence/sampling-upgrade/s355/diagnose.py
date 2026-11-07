"""Replay complete locked s346 and audit the independently bounded actual static caller."""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'a207da0afcf86716d94467b1f6faf52651b9c0f7'
GATES = {
    'target-entry': 'S355_BYTE_BOUND_TARGET_ENTRY_UNPROVED',
    'outer-lifetime': 'S355_INDEPENDENT_OUTER_LIFETIME_UNPROVED',
    'independent-controls': 'S355_INDEPENDENT_CONTROLS_UNPROVED',
    'child-clock': 'S355_CHILD_CLOCK_UNPROVED',
    'fresh-capture': 'S355_FRESH_CAPTURE_BLOCKED',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_pins(path):
    for name, expected in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + name)


def load_prior():
    spec = importlib.util.spec_from_file_location('s355_locked_s346', HERE.parent / 's346/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    return prior


def replay():
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's346/diagnosis.json').read_text()):
        raise ValueError('complete locked s346 diagnosis changed')
    return prior


def audit_route(record):
    if sha((json.dumps(record, indent=2, ensure_ascii=False) + '\n').encode()) != ROUTE_SHA256:
        raise ValueError('caller route changed; independent review required')
    spec = importlib.util.spec_from_file_location('s355_source', HERE / 'extract_route.py')
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    if source.source_callsite((ROOT / 'game/main.swf').read_bytes()) != record['caller']:
        raise ValueError('original caller differs')
    return record


ROUTE_SHA256 = '336a22f82956c75c32fec677f5ac5fa7c2e21e05a36d47a440a7a5e62c1acf52'


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    prior = replay()
    route = audit_route(json.loads((HERE / 'caller-route.json').read_text()))
    return {
        'slice': 's355', 'base': BASE, 'scope': 'AFTER-s353 rank #2 only',
        'authority': 'evidence/sampling-upgrade/next-fix-priority-after-s353.md',
        'production_admitted': False, 'native_parity_proven': False, 'm0_02_status': 'pending',
        'locked_s346_reproduced': True,
        'historical_validation_only': prior['historical_validation_only'],
        'static_caller_derivation': route,
        'independently_observed_disk_facts': ['Original ones operand/call window and containing function', 'Numeric 0x52 table association and 20-byte continuation prefix'],
        'retained_validation_not_new_progress': ['s346 complete diagnosis', 's303 dispatch/table/arm', 'historical placement and 26828 events'],
        'outer_lifetime_assessment': {'channel': None, 'independently_observed': False, 'reason': 'The independent actual-caller route reaches a qword [r13+0xd50] read and byte [rax+0x951] comparison. No mapping from these fields to outer ones, allocation/removal/replacement events or uninterrupted generations is established. Existing Sprite1813 placement inventory is retained validation, not independent lifetime proof. No live lifetime experiment executed.'},
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
        'blocker': 'Original timer operands bind a static ones CallMethod at action offset 660 (0x52), distinct from the s346 0x9f candidate. The numeric dispatch continuation stops at its first unresolved branch. Loaded caller/method resolution, ten-target frame entry and independent outer lifetime remain unproved. Controls and capture stop before execution.',
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
    print('S355_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

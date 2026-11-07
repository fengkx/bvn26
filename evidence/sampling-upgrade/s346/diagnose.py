"""Replay locked ones evidence and report the numeric-dispatch entry derivation attempt."""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'ac99df4d090d97409df7a9f58f039a7f99e93ea5'
GATES = {
    'target-entry': 'S346_BYTE_BOUND_TARGET_ENTRY_UNPROVED',
    'outer-lifetime': 'S346_INDEPENDENT_OUTER_LIFETIME_UNPROVED',
    'independent-controls': 'S346_INDEPENDENT_CONTROLS_UNPROVED',
    'child-clock': 'S346_CHILD_CLOCK_UNPROVED',
    'fresh-capture': 'S346_FRESH_CAPTURE_BLOCKED',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_pins(path):
    for name, expected in json.loads(path.read_text()).items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + name)


def load_prior():
    spec = importlib.util.spec_from_file_location('s346_locked_s337', HERE.parent / 's337/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    return prior


def replay():
    prior = load_prior().diagnose()
    if prior != json.loads((HERE.parent / 's337/diagnosis.json').read_text()):
        raise ValueError('complete locked s337 diagnosis changed')
    return prior


def audit_route(record):
    if sha((json.dumps(record, indent=2) + '\n').encode()) != ROUTE_SHA256:
        raise ValueError('native route changed; independent review required')
    for name, region in record['regions'].items():
        raw = bytes.fromhex(region['hex'])
        if len(raw) != region['end_exclusive'] - region['start'] or sha(raw) != region['sha256']:
            raise ValueError('region bytes differ')
        if sha((HERE / (name + '.txt')).read_bytes()) != region['disassembly_sha256']:
            raise ValueError('disassembly custody differs')
    dispatch = bytes.fromhex(record['dispatch']['hex'])
    if dispatch != bytes.fromhex('4489f883c0fc3d9b0000000f8765feffff488d0db5840000486304814801c8ffe0'):
        raise ValueError('dispatch instructions differ')
    table = 0x124a8f + struct.unpack_from('<i', dispatch, 20)[0]
    if table != record['table'] or record['table_entry']['start'] != table + 4 * (0x9f - 4):
        raise ValueError('table mapping differs')
    target = table + struct.unpack('<i', bytes.fromhex(record['table_entry']['hex']))[0]
    arm = bytes.fromhex(record['regions']['dispatch_arm']['hex'])
    if target != 0x125f31 or arm != bytes.fromhex('488db5a0feffff488bbda8faffff4c89ca4c89c3e876a5ffff'):
        raise ValueError('arm bytes differ')
    call_target = 0x125f4a + struct.unpack_from('<i', arm, 21)[0]
    prefix = bytes.fromhex(record['regions']['callee_prefix']['hex'])
    if call_target != 0x1204c0 or prefix != bytes.fromhex('554889e54157415641554154534883ec184989d74989f44889fb8b8320050000b90200000085c0741b'):
        raise ValueError('callee prefix differs')
    return dict(table_relative=table, opcode=0x9f, target_relative=target,
                direct_call_relative=0x125f45, callee_relative=call_target,
                first_branch_relative=0x1204e7, branch_target_relative=0x120504,
                fallthrough_relative=0x1204e9,
                argument_relations=['rsi = address of caller [rbp-0x160]',
                                    'rdi = qword caller [rbp-0x558]', 'rdx = r9'],
                callee_relations=['r15 = incoming rdx', 'r12 = incoming rsi',
                                 'rbx = incoming rdi', 'eax = dword [rbx+0x520]',
                                 'test eax,eax; je 0x120504'],
                target_entry_proved=False, outer_lifetime_proved=False,
                limitation='Numeric opcode arm candidate only. No loaded ones callsite-to-opcode association, frame entry effect, ten-frame coverage, native object layout or lifetime channel. Stop at first callee branch; neither successor expanded.')


ROUTE_SHA256 = '6e592363e57aeb63f6b0146203d8e4c4004c481030e0e6b29f5f1d3bb7bb856d'


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    prior = replay()
    route = audit_route(json.loads((HERE / 'native-route.json').read_text()))
    return {
        'slice': 's346', 'base': BASE, 'scope': 'AFTER-s344 rank #2 only',
        'authority': 'evidence/sampling-upgrade/next-fix-priority-after-s344.md',
        'production_admitted': False, 'native_parity_proven': False, 'm0_02_status': 'pending',
        'locked_s337_reproduced': True,
        'historical_validation_only': prior['historical_validation_only'],
        'native_derivation_attempt': route,
        'outer_lifetime_assessment': {'channel': None, 'independently_observed': False, 'reason': 'The arm passes r9 as rdx; the callee copies it to r15. This is register transport only, with no clip layout, allocation/free hooks, loaded binding or replacement-surviving generation. No separate live lifetime experiment executed.'},
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
        'blocker': 'The numeric 0x9f dispatch arm reaches a direct call and its first callee branch, but no loaded ones callsite association or actual frame-entry effect is derived. Ten-frame coverage and independent outer lifetime remain unproved. Static argument transport is not object identity. Controls and fresh capture remain blocked before execution.',
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
    print('S346_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

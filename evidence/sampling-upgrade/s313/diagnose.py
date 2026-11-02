"""Audit the locked read wrapper's unresolved consumer/request boundary."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '435d7f2aa60ba81e5c754fc45c984ff4f92984af'
GATES = {
    'consumer-request': 'S313_CONSUMER_REQUEST_UNPROVED',
    'loader-attestation': 'S313_LOADER_ASSOCIATION_UNPROVED',
    'pre-advance-target': 'S313_PRE_ADVANCE_TARGET_UNPROVED',
    'wrong-resource-control': 'S313_WRONG_RESOURCE_BLOCKED',
}
EXCLUSIONS = [
    'static hash as live bytes', 'mutable request proxy', 'helper stamp',
    'global counter', 'receipt resealing', 'rollout', 'ranks 1-4 and 6-9',
    's254-s312 edits', 'game/scripts/runtime/contracts/shared sampler/threshold/validator changes',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def locked_module():
    spec = importlib.util.spec_from_file_location('s306_locked', HERE.parent / 's306/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_boundary(record, transcript, stub):
    # Reuse the locked complete-byte check before interpreting additional sites.
    locked_module().audit_wrapper(record, transcript, stub)
    raw = bytes.fromhex(record['wrapper']['hex'])
    start = record['wrapper']['address']
    witnesses = []
    for address, code, fact in [
        (0x1004b3595, '4589f5', 'r14d copied into r13d at shared exit'),
        (0x1004b35c0, '48c7431800000000', 'cleanup path writes zero to rbx+0x18'),
        (0x1004b35c8, '488bbba0000000', 'exit call argument loaded from rbx+0xa0'),
        (0x1004b35d4, '4489e8', 'r13d copied into eax after exit call'),
        (0x1004b35e5, 'c3', 'wrapper returns to an unresolved caller'),
        (0x1004b35e6, '4189c6', 'positive API result eax copied into r14d'),
    ]:
        if raw[address - start:address - start + len(bytes.fromhex(code))].hex() != code:
            raise ValueError('changed boundary operand: ' + hex(address))
        witnesses.append({'address': hex(address), 'hex': code, 'static_fact': fact})
    calls = []
    returns = []
    rows = re.findall(r'Debugger\[(0x[0-9a-f]+)\] <\+\d+>:\s+((?:[0-9a-f]{2} )+)\s+([^\n]+)', transcript)
    for address, code, instruction in rows:
        address = int(address, 16)
        code = bytes.fromhex(code)
        if instruction.startswith('callq'):
            if code[0] == 0xe8 and len(code) == 5:
                target = hex(address + 5 + int.from_bytes(code[1:], 'little', signed=True))
                kind = 'direct_relative'
            elif code == bytes.fromhex('ff9000040000'):
                target, kind = None, 'indirect_rax_plus_0x400'
            else:
                raise ValueError('unclassified call encoding')
            calls.append({'address': hex(address), 'hex': code.hex(),
                          'kind': kind, 'static_target': target,
                          'return_site': hex(address + len(code)),
                          'executed_target': None, 'p1_consumer_identity': None})
        if code == b'\xc3':
            returns.append(hex(address))
    if len(calls) != 16 or returns != ['0x1004b35e5']:
        raise ValueError('changed complete call/return inventory')
    return {
        'kind': 'static_boundary_audit_not_live_attestation',
        'witnesses': witnesses, 'calls': calls, 'returns': returns,
        'indirect_call_sites': [c['address'] for c in calls if c['static_target'] is None],
        'candidate_api_return': '0x1004b3552',
        'candidate_wrapper_return': '0x1004b35e5',
        'caller_continuation': None, 'actual_p1_consumer': None,
        'immutable_request_generation': None,
        'limitation': 'Return-register copies do not identify a consumer. The exit contains an external call whose effects are unqualified. The cleared stream slot is mutable, not a generation identity. No native class or ABI-level preservation is inferred.',
    }


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    prior = locked_module().diagnose()
    if prior != json.loads((HERE.parent / 's306/diagnosis.json').read_text()):
        raise ValueError('locked s306 diagnosis mismatch')
    record = json.loads((HERE.parent / 's306/native-bytes.json').read_text())
    stub = json.loads((HERE.parent / 's297/diagnosis.json').read_text())['static_read_stubs'][0]
    boundary = audit_boundary(record, (HERE.parent / 's306/read-wrapper.txt').read_text(), stub)
    return {
        'base': BASE, 'scope': 'AFTER-s308 rank #5 only; s259-normal P1',
        'production_admitted': False, 'native_parity_proven': False,
        'M0-02': 'pending', 'product_obligations_closed': 0,
        'locked_s306_reproduced': True, 'historical_normal': prior['historical_normal'],
        'source_loader_order': prior['source_loader_order'],
        'consumer_boundary_audit': boundary,
        'observations': {**prior['observations'], 'consumed_buffer_ranges': None,
                         'observer_effects': None},
        'consumer_request_proved': False, 'loader_attestation_proved': False,
        'normal_association_qualified': False, 'pre_advance_target_proved': False,
        'wrong_resource_control_qualified': False, 'wrong_resource_control_executed': False,
        'first_unmet_prerequisite': 'actual P1 consumer and immutable request generation',
        'blocker': 'No executed P1 consumer/request resolver. API return, wrapper return and mutable stream slot do not join returned/consumed ranges to an immutable request and target before inline loadStep advance.',
        'next_discriminator': 'Independently resolve one actual P1 consumer and request generation; bind executed returned/consumed ranges and callback target before loadStep++. Qualify observer effects and same-request init/use/unload/replacement. Only then run separate Yihu-for-Yijiao control with expected Yijiao identity unchanged.',
        'new_builds': 0, 'new_player_launches': 0, 'new_process_attaches': 0,
        'new_captures': 0, 'new_memory_reads': 0,
        'exclusions_enforced': EXCLUSIONS,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, 'S313_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + ': ' + report['blocker'] + '\n')
    print('S313_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')


if __name__ == '__main__':
    main()

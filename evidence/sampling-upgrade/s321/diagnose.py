"""Audit one static Loader caller candidate without promoting it to live proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '49ccb1065788ef98ddf9facc5bb7a5ede003916e'
GATES = {
    'consumer-request': 'S321_CONSUMER_REQUEST_UNPROVED',
    'loader-attestation': 'S321_LOADER_ASSOCIATION_UNPROVED',
    'pre-advance-target': 'S321_PRE_ADVANCE_TARGET_UNPROVED',
    'wrong-resource-control': 'S321_WRONG_RESOURCE_BLOCKED',
}
WINDOW = 'c6401000c645d700488b38ba01000000488d75d7e8d3a43a000fb64dd788ca80e20180fa014519ed4509f583f8ff440f44e848c1e10481e1e00f000048898b40010000488bbbd8010000488b07ff9000040000'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def locked_module():
    spec = importlib.util.spec_from_file_location('s313_locked', HERE.parent / 's313/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_window(record, transcript):
    w = record['window']
    if (w['address'], w['end_exclusive'], w['file_offset'], w['hex']) != (
            0x100108f54, 0x100108fa7, 0x108f54, WINDOW):
        raise ValueError('changed caller window')
    if record['kind'] != 'static_file_bytes_not_executed_or_consumed_bytes':
        raise ValueError('static evidence cannot be promoted')
    rows = re.findall(r'^([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s+([^\n]+)', transcript, re.M)
    cursor = w['address']
    raw = bytes.fromhex(WINDOW)
    instructions = []
    for address, code, text in rows:
        address, code = int(address, 16), bytes.fromhex(code)
        if address != cursor or code != raw[cursor - w['address']:cursor - w['address'] + len(code)]:
            raise ValueError('instruction coverage mismatch')
        instructions.append(dict(address=hex(address), hex=code.hex(), instruction=text.strip()))
        cursor += len(code)
    if cursor != w['end_exclusive'] or len(instructions) != 20:
        raise ValueError('incomplete instruction coverage')
    call = raw[0x14:0x19]
    target = 0x100108f68 + 5 + int.from_bytes(call[1:], 'little', signed=True)
    if call[0] != 0xe8 or target != record['target'] or target != 0x1004b3440:
        raise ValueError('changed wrapper target')
    return dict(kind='static_candidate_only', instructions=instructions,
                call_site='0x100108f68', wrapper_target=hex(target),
                argument_buffer='address of caller rbp-0x29', argument_length=1,
                buffer_initialization='zero at 0x100108f58 before call',
                post_call_read='movzx ecx, byte ptr [rbp-0x29] at 0x100108f6d',
                derived_store='(zero-extended byte << 4) & 0xfe0 to [rbx+0x140] at 0x100108f90',
                next_opaque_call='[rax+0x400] at 0x100108fa1',
                limitation='Conditional on normal wrapper return. The local can still contain its initialized zero on failure; a post-call load does not prove returned-byte provenance. No executed path, P1 identity, class, generation or target inferred.')


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    prior = locked_module().diagnose()
    if prior != json.loads((HERE.parent / 's313/diagnosis.json').read_text()):
        raise ValueError('locked s313 diagnosis mismatch')
    record = json.loads((HERE / 'native-audit.json').read_text())
    candidate = audit_window(record, (HERE / 'caller-window.txt').read_text())
    return dict(base=BASE, scope='AFTER-s317 rank #4 only', production_admitted=False,
                native_parity_proven=False, **{'M0-02': 'pending'}, product_obligations_closed=0,
                locked_s313_reproduced=True, historical_normal=prior['historical_normal'],
                source_loader_order=prior['source_loader_order'],
                static_candidate=candidate, pattern_scan=record['scan'],
                observations={**prior['observations'], 'executed_caller': None,
                              'immutable_request_generation': None},
                consumer_request_proved=False, loader_attestation_proved=False,
                normal_association_qualified=False, pre_advance_target_proved=False,
                wrong_resource_control_executed=False, wrong_resource_control_qualified=False,
                first_unmet_prerequisite='actual P1 consumer and immutable request generation',
                blocker='One static buffer-read candidate is bounded; actual caller/P1/request ownership and executed returned/consumed ranges before inline advance remain absent. Normal must qualify before wrong-resource control.',
                new_builds=0, new_player_launches=0, new_process_attaches=0,
                new_captures=0, new_memory_reads=0,
                exclusions=['return-register copy as consumption', 'mutable slot as generation',
                            'static hash as live bytes', 'helper stamp', 'receipt resealing',
                            'rollout', 'other ranks', 'prior evidence edits', 'runtime changes'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, 'S321_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = [code for flag, code in GATES.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + ': ' + report['blocker'] + '\n')
    print('S321_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')


if __name__ == '__main__':
    main()

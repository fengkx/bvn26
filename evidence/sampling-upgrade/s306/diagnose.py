"""Bound one static read wrapper without promoting it to an executed P1 join."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'caaec62ce3e60bf87418bc727490419e963851d8'
START, END = 0x1004b3440, 0x1004b35f0
EXCLUSIONS = ['static hash as live bytes', 'mutable request proxy', 'helper stamp',
              'global counter', 'receipt resealing', 'rollout', 'ranks 1-6 and 8-9',
              'game/scripts/runtime/contracts/shared sampler/threshold/validator changes',
              's254-s305 edits']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_wrapper(record, transcript, stub):
    if record['kind'] != 'static_file_bytes_not_executed_or_consumed_bytes':
        raise ValueError('static evidence cannot become execution evidence')
    wrapper = record['wrapper']
    raw = bytes.fromhex(wrapper['hex'])
    if (wrapper['address'], wrapper['size']) != (START, END - START) or len(raw) != END - START:
        raise ValueError('incomplete wrapper boundary')
    for region in (wrapper, record['stub']):
        if sha(bytes.fromhex(region['hex'])) != region['sha256']:
            raise ValueError('changed native bytes')
        segment = record['text_segment']
        offset = region['address'] - segment['address']
        if not 0 <= offset <= segment['file_size'] - region['size'] or region['file_offset'] != segment['file_offset'] + offset:
            raise ValueError('wrong file/address mapping')
    if record['stub']['address'] != int(stub['unslid_stub'], 16) or record['stub']['hex'] != stub['instruction_hex']:
        raise ValueError('different locked read stub')
    # Require contiguous LLDB instruction bytes for the entire function, including padding.
    rows = re.findall(r'Debugger\[(0x[0-9a-f]+)\] <\+\d+>:\s+((?:[0-9a-f]{2} )+)\s+([^\n]+)', transcript)
    cursor = START
    for address, code, _ in rows:
        code = bytes.fromhex(code)
        if int(address, 16) != cursor or raw[cursor - START:cursor - START + len(code)] != code:
            raise ValueError('disassembly byte coverage mismatch')
        cursor += len(code)
    if cursor != END:
        raise ValueError('incomplete disassembly')

    def require(address, code):
        expected = bytes.fromhex(code)
        if raw[address - START:address - START + len(expected)] != expected:
            raise ValueError('changed operand or branch at ' + hex(address))

    facts = [
        (0x1004b3451, '4189d4', 'entry edx saved in r12d'),
        (0x1004b3454, '488975d0', 'entry rsi saved at rbp-0x30'),
        (0x1004b3458, '4889fb', 'entry rdi saved in rbx; native type unknown'),
        (0x1004b3489, '4963c4', 'saved length sign-extended to rax'),
        (0x1004b348c, '488945c8', 'length saved at rbp-0x38'),
        (0x1004b3541, '488b7b18', 'stream argument read from rbx+0x18'),
        (0x1004b3545, '488b75d0', 'buffer argument restored to rsi'),
        (0x1004b3549, '488b55c8', 'requested length restored to rdx'),
        (0x1004b3552, '4885c0', 'test API return rax before sign/nonzero branches'),
        (0x1004b35e6, '4189c6', 'positive return path copies eax into r14d'),
    ]
    for address, code, _ in facts:
        require(address, code)
    branches = []
    for address, opcode, width in [(0x1004b354d, b'\xe8', 4),
                                    (0x1004b3555, b'\x78', 1),
                                    (0x1004b3557, b'\x0f\x85', 4),
                                    (0x1004b35e9, b'\xeb', 1)]:
        require(address, opcode.hex())
        at = address - START + len(opcode)
        displacement = int.from_bytes(raw[at:at + width], 'little', signed=True)
        branches.append({'instruction': hex(address), 'next_instruction': hex(address + len(opcode) + width),
                         'target': hex(address + len(opcode) + width + displacement)})
    if [b['target'] for b in branches] != [stub['unslid_stub'], '0x1004b3592', '0x1004b35e6', '0x1004b3592']:
        raise ValueError('changed call/branch destination')
    return {'wrapper_start': hex(START), 'wrapper_end_exclusive': hex(END),
            'instruction_count': len(rows), 'bytes_checked': len(raw),
            'operand_facts': [{'address': hex(a), 'hex': b, 'static_fact': c} for a, b, c in facts],
            'branches': branches, 'api_return_site_candidate': '0x1004b3552',
            'live_p1_membership': None, 'native_consumer_type': None,
            'immutable_request_field': None, 'callback_target_resolver': None,
            'limitation': 'Static register/branch facts only. Entry arguments, rbx+0x18 and the returned buffer have no observed P1 identity, generation, contents or consumer. Indirect callers and alternate read/mapped paths remain unresolved.'}


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    prior = load_module('s297_locked', HERE.parent / 's297/diagnose.py').diagnose()
    if prior != json.loads((HERE.parent / 's297/diagnosis.json').read_text()):
        raise ValueError('locked s297 diagnosis mismatch')
    record = json.loads((HERE / 'native-bytes.json').read_text())
    facility = json.loads((HERE / 'facility.json').read_text())
    if record['binary_sha256'] != prior['facility']['binary_sha256']:
        raise ValueError('different player executable')
    binary = prior['facility']['binary']
    expected_command = ['lldb', '--batch', '-o', 'settings set target.preload-symbols false',
                        '-o', f'target create --no-dependents "{binary}"',
                        '-o', 'disassemble --address 0x1004b354d --bytes']
    if facility['command'] != expected_command or facility['exit'] != 0:
        raise ValueError('changed static facility command/outcome')
    if any(facility[k] != 0 for k in ('player_launches', 'process_attaches', 'new_captures')):
        raise ValueError('new execution requires independent analysis')
    transcript = (HERE / facility['log']).read_text()
    if sha(transcript.encode()) != facility['sha256'] or f"Current executable set to '{binary}' (x86_64)." not in transcript:
        raise ValueError('changed facility transcript or failed target')
    raw_transcript = json.loads((HERE / facility['raw_log']).read_text())['transcript']
    normalized = '\n'.join(line.rstrip() for line in raw_transcript.splitlines()) + '\n'
    if sha(raw_transcript.encode()) != facility['raw_transcript_sha256'] or normalized != transcript:
        raise ValueError('changed raw transcript or normalization')
    stub = next(s for s in prior['static_read_stubs'] if s['symbol'] == 'CFReadStreamRead')
    result = audit_wrapper(record, transcript, stub)
    return {
        'base': BASE, 'scope': 'AFTER-s299 rank #7 only; s259-normal P1',
        'production_admitted': False, 'native_parity_proven': False,
        'loader_attestation_proved': False, 'normal_association_qualified': False,
        'pre_advance_target_proved': False, 'wrong_resource_control_qualified': False,
        'wrong_resource_control_executed': False, 'product_obligations_closed': 0,
        'M0-02': 'pending', 'locked_s297_reproduced': True,
        'historical_normal': prior['historical_normal'],
        'source_loader_order': prior['source_loader_order'],
        'static_wrapper_audit': result, 'observations': dict(prior['observations']),
        'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0,
        'new_process_attaches': 0, 'new_metadata_name_queries': 0,
        'exclusions_enforced': EXCLUSIONS,
        'blocker': 'No executed P1 returned-byte/consumer/immutable-request/target join before inline loadStep advance. The static wrapper supplies candidate argument/return locations, not live values or a P1 resolver.',
        'wrong_resource_blocker': 'Independent normal qualification missing; separate actual Yihu-for-Yijiao control not executed.',
        'next_discriminator': 'Identify the actual P1 native consumer and immutable request generation independently of this candidate; then retain complete returned/consumed ranges and request-bound target before loadStep++. Qualify observer effects, same-request init/use and unload/replacement before a separate wrong-resource control. Do not guess rbx fields or treat a breakpoint hit as the join.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    gates = {'loader-attestation': 'S306_LOADER_ASSOCIATION_UNPROVED',
             'pre-advance-target': 'S306_PRE_ADVANCE_TARGET_UNPROVED',
             'wrong-resource-control': 'S306_WRONG_RESOURCE_BLOCKED'}
    for flag in gates:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = [code for flag, code in gates.items() if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        parser.exit(1, '\n'.join(failures) + ': ' + report['blocker'] + '\n')
    print('S306_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')


if __name__ == '__main__':
    main()

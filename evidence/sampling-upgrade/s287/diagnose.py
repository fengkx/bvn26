"""Audit one P1 loader prerequisite without admitting static data as live proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
READS = {'read', 'fread', 'mmap', 'CFReadStreamRead'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit_read_stubs(indirect, disassembly):
    symbols = {}
    for address, name in re.findall(
            r'^(0x[0-9a-f]+)\s+\d+\s+_(read|fread|mmap|CFReadStreamRead)$', indirect, re.M):
        symbols[int(address, 16)] = name
    rows = []
    for address, raw in re.findall(
            r'Debugger\[(0x[0-9a-f]+)\] <\+0>: ((?:[0-9a-f]{2} ){6})', disassembly):
        address = int(address, 16)
        code = bytes.fromhex(raw)
        if code[:2] != b'\xff\x25':
            raise ValueError('not an indirect RIP-relative jump')
        slot = address + 6 + struct.unpack('<i', code[2:])[0]
        if address not in symbols or symbols.get(slot) != symbols[address]:
            raise ValueError('read stub/slot symbol mismatch')
        rows.append({'symbol': symbols[address], 'unslid_stub': hex(address),
                     'unslid_pointer_slot': hex(slot), 'instruction_hex': code.hex()})
    if len(rows) != 4 or {row['symbol'] for row in rows} != READS:
        raise ValueError('missing or duplicated read stubs')
    return rows


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    facility = json.loads((HERE / 'facility.json').read_text())
    for check in facility['checks']:
        if sha((HERE / check['log']).read_bytes()) != check['sha256']:
            raise ValueError('facility transcript changed: ' + check['log'])
    spec = importlib.util.spec_from_file_location('s277_locked', HERE.parent / 's277/diagnose.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    replay = prior.diagnose()
    if facility['binary_sha256'] != replay['facility']['binary_sha256']:
        raise ValueError('different player executable')
    if (facility['player_launches'], facility['process_attaches'], facility['live_read_events']) != (0, 0, None):
        raise ValueError('new execution evidence requires independent analysis')
    return {
        'base': '2e92fccd', 'scope': 'AFTER-s281 rank 6 only; s259-normal P1',
        'production_admitted': False, 'native_parity_proven': False,
        'loader_attestation_proved': False, 'product_obligations_closed': 0,
        'historical_normal': replay['historical_normal'],
        'source_loader_order': replay['source_loader_order'],
        'static_read_stubs': audit_read_stubs((HERE / 'indirect-symbols.txt').read_text(),
                                            (HERE / 'read-addresses.txt').read_text()),
        'facility': facility,
        'observations': {key: None for key in (
            'executed_read_return', 'returned_buffer_ranges', 'loader_consumer',
            'immutable_request_identity', 'target_before_loadStep_advance',
            'same_request_initialization', 'target_lifetime', 'actual_wrong_resource_control')},
        'new_builds': 0, 'new_captures': 0,
        'wrong_resource_control_qualified': False,
        'missing': ['Executed read-return and complete returned-byte ranges',
                    'Native consumer/request association before completion advances loadStep',
                    'Same-request completion target, initialization and bounded lifetime',
                    'Separately qualified actual Yihu-for-Yijiao load control'],
        'limitation': 'Static import jumps identify neither an executed API nor a consuming loader request. Symbol lookup failure is not proof that debugging is impossible. No live bytes or request/target join were observed.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-loader-attestation', action='store_true')
    parser.add_argument('--require-wrong-resource-control', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.require_loader_attestation or args.require_wrong_resource_control:
        parser.exit(1, 'S287_LOADER_UNPROVED: ' + '; '.join(report['missing']) + '\n')
    print('S287_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')


if __name__ == '__main__':
    main()

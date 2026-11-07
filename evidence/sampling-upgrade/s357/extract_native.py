"""Bound the first nonzero return-arm continuation without inferring object types."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
START, END = 0x125003, 0x125014
EXPECTED = bytes.fromhex('80784000488b95a8faffff0f8532210000')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract(raw):
    prior = load('s357_prior_route', HERE.parent / 's350/extract_native.py')
    retained = prior.extract(raw)
    prior.audit_record(retained)
    macho = load('s357_macho', HERE.parent / 's303/audit_native.py')
    offset = macho.file_offset(macho.macho(raw), retained['image_base'] + START, END - START)
    data = raw[offset:offset + END - START]
    if data != EXPECTED:
        raise ValueError('First continuation bytes differ')
    return dict(binary_sha256=sha(raw), binary_size=len(raw),
                module_uuid=retained['module_uuid'], image_base=retained['image_base'],
                predecessor='evidence/sampling-upgrade/s350/native-route.json',
                predecessor_branch=0x124ffd, target=START,
                entry_condition='s350 [rax+0x58] load result is nonzero; not observed live',
                regions={'first_continuation': dict(start=START, end_exclusive=END,
                         file_offset=offset, hex=data.hex(), sha256=sha(data))},
                branch_target=END + struct.unpack_from('<i', data, 13)[0],
                fallthrough=END,
                frontier='Untyped [rax+0x40] byte and [rbp-0x558] value; no loaded callback/owner/activation association',
                loaded_closure_body=None, owner_generation=None, activation=None,
                matched_dispatcher_continuation=None, replacement_survival=None,
                native_observations=[], new_player_launches=0, new_attaches=0,
                new_memory_reads=0, successor_expansions=0)


def audit_record(record):
    # The pinned record preserves disassembly custody as well as every unknown.
    expected = json.loads((HERE / 'native-route.json').read_text())
    if record != expected:
        raise ValueError('Continuation record changed')
    region = record['regions']['first_continuation']
    if (region['start'], region['end_exclusive'], region['hex'], region['sha256']) != (
            START, END, EXPECTED.hex(), sha(EXPECTED)):
        raise ValueError('Continuation byte bounds changed')
    if record['branch_target'] != 0x127146 or record['fallthrough'] != END:
        raise ValueError('Branch operands changed')
    for key in ('loaded_closure_body', 'owner_generation', 'activation',
                'matched_dispatcher_continuation', 'replacement_survival'):
        if record[key] is not None:
            raise ValueError('Disk bytes promoted to live identity')
    if record['native_observations']:
        raise ValueError('Unobserved execution')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    record = extract(args.binary.read_bytes())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    command = ['objdump', '-d', '--x86-asm-syntax=intel',
               '--start-address=' + hex(record['image_base'] + START),
               '--stop-address=' + hex(record['image_base'] + END), str(args.binary)]
    result = subprocess.run(command, capture_output=True, check=True, timeout=60)
    log = (result.stdout + result.stderr).replace(str(args.binary).encode(), b'<receipt-pinned-player>')
    (args.output_dir / 'first_continuation.txt').write_bytes(log)
    record['regions']['first_continuation'].update(
        disassembly_sha256=sha(log), command=command[:-1] + ['<receipt-pinned-player>'])
    (args.output_dir / 'native-route.json').write_text(json.dumps(record, indent=2) + '\n')
    print('S357_CONTINUATION_EXTRACTED; loaded identities/effects unproved')


if __name__ == '__main__':
    main()

"""Read a numeric dispatch route from the receipt-pinned disk player, without names."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
OPCODE = 0x3e
# Stop at the first conditional transfer; neither successor is explored.
WINDOWS = {'return_arm_prefix': (0x124fef, 0x125003)}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def extract(raw):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    if sha(raw) != locked['binary_sha256']:
        raise ValueError('binary differs from locked receipt')
    spec = importlib.util.spec_from_file_location('s350_macho', HERE.parent / 's303/audit_native.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata = module.macho(raw)
    if metadata != locked['module']:
        raise ValueError('Mach-O metadata differs')
    base = locked['image_base']

    def region(start, end):
        offset = module.file_offset(metadata, base + start, end - start)
        data = raw[offset:offset + end - start]
        return dict(start=start, end_exclusive=end, file_offset=offset,
                    hex=data.hex(), sha256=sha(data))

    # Re-read the retained fetch/dispatch and table; they are not new progress.
    for name in ('fetch_and_dispatch', 'dispatch_table'):
        old = locked['regions'][name]
        if region(old['module_relative'], old['module_relative'] + old['size'])['hex'] != old['hex']:
            raise ValueError('retained dispatcher differs')
    dispatch = region(0x124a77, 0x124a98)
    table = 0x124a8f + struct.unpack_from('<i', bytes.fromhex(dispatch['hex']), 20)[0]
    entry = region(table + 4 * (OPCODE - 4), table + 4 * (OPCODE - 4) + 4)
    target = table + struct.unpack('<i', bytes.fromhex(entry['hex']))[0]
    if target != WINDOWS['return_arm_prefix'][0]:
        raise ValueError('numeric dispatch target differs')
    regions = {name: region(*bounds) for name, bounds in WINDOWS.items()}
    return dict(binary_sha256=sha(raw), binary_size=len(raw), module_uuid=metadata['uuid'],
                image_base=base, opcode=OPCODE, dispatch=dispatch, table=table, table_entry=entry,
                target=target, regions=regions, new_name_searches=0,
                new_player_launches=0, new_attaches=0, new_memory_reads=0,
                loaded_closure_body=None, owner_generation=None, activation=None,
                matched_dispatcher_continuation=None, replacement_survival=None,
                native_observations=[])


def audit_record(record):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    if record['binary_sha256'] != locked['binary_sha256']:
        raise ValueError('player receipt mismatch')
    dispatch = record['dispatch']
    if dispatch['hex'] != locked['regions']['fetch_and_dispatch']['hex'][-66:]:
        raise ValueError('dispatch bytes mismatch')
    table = 0x124a8f + struct.unpack_from('<i', bytes.fromhex(dispatch['hex']), 20)[0]
    old_table = locked['regions']['dispatch_table']
    offset = table + 4 * (OPCODE - 4) - old_table['module_relative']
    entry = bytes.fromhex(old_table['hex'])[offset:offset + 4]
    if record['table_entry']['hex'] != entry.hex() or record['table'] != table:
        raise ValueError('numeric table entry mismatch')
    if record['target'] != table + struct.unpack('<i', entry)[0] or record['opcode'] != OPCODE:
        raise ValueError('numeric route mismatch')
    region = record['regions']['return_arm_prefix']
    expected = bytes.fromhex('488b8598faffff488b40584885c00f8427210000')
    if (region['start'], region['end_exclusive']) != WINDOWS['return_arm_prefix']:
        raise ValueError('bounded window changed')
    if region['hex'] != expected.hex() or region['sha256'] != sha(expected):
        raise ValueError('bounded bytes changed')
    for key in ('loaded_closure_body', 'owner_generation', 'activation',
                'matched_dispatcher_continuation', 'replacement_survival'):
        if record[key] is not None:
            raise ValueError('disk route promoted to live proof')
    if record['native_observations'] != []:
        raise ValueError('unobserved native event')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    record = extract(args.binary.read_bytes())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, (start, end) in WINDOWS.items():
        command = ['objdump', '-d', '--x86-asm-syntax=intel',
                   '--start-address=' + hex(record['image_base'] + start),
                   '--stop-address=' + hex(record['image_base'] + end), str(args.binary)]
        result = subprocess.run(command, capture_output=True, check=True, timeout=60)
        log = (result.stdout + result.stderr).replace(str(args.binary).encode(), b'<receipt-pinned-player>')
        (args.output_dir / (name + '.txt')).write_bytes(log)
        record['regions'][name]['disassembly_sha256'] = sha(log)
        record['regions'][name]['command'] = command[:-1] + ['<receipt-pinned-player>']
    (args.output_dir / 'native-route.json').write_text(json.dumps(record, indent=2) + '\n')
    print('S350_DISK_ROUTE_EXTRACTED; closure/owner/activation and continuation unproved')


if __name__ == '__main__':
    main()

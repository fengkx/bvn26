"""Read the unresolved Loader wrapper exit callee from the receipt-pinned player."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
WINDOWS = {'exit_callee': (0x498d20, 0x498d52)}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def extract(raw):
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    if sha(raw) != locked['binary_sha256']:
        raise ValueError('binary differs from locked receipt')
    spec = importlib.util.spec_from_file_location('s348_macho', HERE.parent / 's303/audit_native.py')
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

    # The retained exit call is an anchor, never new execution evidence.
    anchor = region(0x4b35c8, 0x4b35d7)
    if anchor['hex'] != '488bbba0000000e84c57feff4489e8':
        raise ValueError('retained exit call differs')
    call = bytes.fromhex(anchor['hex'])[7:12]
    target = 0x4b35d4 + struct.unpack('<i', call[1:])[0]
    if target != WINDOWS['exit_callee'][0]:
        raise ValueError('exit callee destination differs')
    return dict(binary_sha256=sha(raw), binary_size=len(raw), module_uuid=metadata['uuid'],
                image_base=base, wrapper_anchor=anchor, wrapper_call_target=target,
                regions={name: region(*bounds) for name, bounds in WINDOWS.items()},
                kind='static_file_bytes_not_executed_or_consumed_bytes',
                discovery_window_bytes=128, retained_new_bytes=50,
                new_player_launches=0, new_attaches=0, new_memory_reads=0)


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
        log = result.stdout + result.stderr
        (args.output_dir / (name + '.txt')).write_bytes(log)
        record['regions'][name]['disassembly_sha256'] = sha(log)
        record['regions'][name]['command'] = command
    (args.output_dir / 'native-route.json').write_text(json.dumps(record, indent=2) + '\n')
    print('S348_DISK_ROUTE_EXTRACTED; executed P1 consumer/request/range/target unproved')


if __name__ == '__main__':
    main()

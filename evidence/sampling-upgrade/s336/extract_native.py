"""Extract the two fixed immediate successor windows of the s327 frontier from the locked disk binary."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
WINDOWS = ((0xd2244, 0xd226d), (0xd2254, 0xd226d))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    raw = args.binary.read_bytes()
    if hashlib.sha256(raw).hexdigest() != locked['binary_sha256']:
        raise ValueError('Binary does not match locked receipt')
    spec = importlib.util.spec_from_file_location('s336_macho', HERE.parent / 's303/audit_native.py')
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    module = decoder.macho(raw)
    if module != locked['module']:
        raise ValueError('Mach-O metadata differs')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for start, end in WINDOWS:
        offset = decoder.file_offset(module, locked['image_base'] + start, end - start)
        data = raw[offset:offset + end - start]
        command = ['objdump', '-d', '--x86-asm-syntax=intel',
                   '--start-address=' + hex(locked['image_base'] + start),
                   '--stop-address=' + hex(locked['image_base'] + end), str(args.binary)]
        result = subprocess.run(command, capture_output=True, check=True, timeout=60)
        log = result.stdout + result.stderr
        name = 'successor-' + hex(start) + '.txt'
        (args.output_dir / name).write_bytes(log)
        reports.append(dict(start=start, end_exclusive=end, file_offset=offset,
                            hex=data.hex(), sha256=decoder.sha(data),
                            disassembly_sha256=decoder.sha(log), log=name,
                            command=command, exit_code=result.returncode))
    report = dict(binary=str(args.binary), binary_sha256=locked['binary_sha256'],
                  binary_size=len(raw), module_uuid=module['uuid'], image_base=locked['image_base'],
                  windows=reports, wall_seconds=time.monotonic() - started,
                  discovery='128-byte discovery per s327 successor; retain only through first transfer. The fallthrough window crosses the known join at 0xd2254; overlapping suffix is counted once.',
                  new_player_launches=0, new_memory_reads=0)
    (args.output_dir / 'native-audit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()

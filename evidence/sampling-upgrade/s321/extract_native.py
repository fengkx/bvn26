"""Locate byte-pattern caller candidates and extract one bounded continuation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
TARGET = 0x1004b3440
BEGIN, END = 0x100108f54, 0x100108fa7


def candidates(raw, begin, end, base, target):
    # Patterns are not instruction-boundary proof or an exhaustive caller graph.
    return [i for match in re.finditer(b'[\xe8\xe9]', raw[begin:end])
            if (i := begin + match.start()) + 5 <= end
            and base + i + 5 + int.from_bytes(raw[i + 1:i + 5], 'little', signed=True) == target]


def main():
    started = time.monotonic()
    lock = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    raw = Path(lock['binary']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != lock['binary_sha256']:
        raise ValueError('receipt binary mismatch')
    spec = importlib.util.spec_from_file_location('macho', HERE.parent / 's303/audit_native.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata = module.macho(raw)
    if metadata != lock['module']:
        raise ValueError('module metadata mismatch')
    header = bytes.fromhex(metadata['header_hex'])
    section = header.index(b'__text' + bytes(10))
    import struct
    address, size, offset = struct.unpack_from('<QQI', header, section + 32)
    found = candidates(raw, offset, offset + size, address - offset, TARGET)
    start = module.file_offset(metadata, BEGIN, END - BEGIN)
    command = ['objdump', '-d', '--x86-asm-syntax=intel', '--start-address=' + hex(BEGIN),
               '--stop-address=' + hex(END), lock['binary']]
    result = subprocess.run(command, capture_output=True, check=True, timeout=60)
    (HERE / 'caller-window.txt').write_bytes(result.stdout + result.stderr)
    report = dict(binary=lock['binary'], binary_sha256=lock['binary_sha256'],
                  module_uuid=metadata['uuid'], target=TARGET,
                  scan=dict(file_offset=offset, size=size, address=address,
                            candidate_file_offsets=found, instruction_boundaries_proved=False),
                  window=dict(address=BEGIN, end_exclusive=END, file_offset=start,
                              hex=raw[start:start + END - BEGIN].hex()),
                  command=command, exit_code=result.returncode,
                  elapsed_seconds=time.monotonic() - started,
                  kind='static_file_bytes_not_executed_or_consumed_bytes')
    (HERE / 'native-audit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()

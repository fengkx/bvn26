"""Extract bounded native candidates from the receipt-pinned Mach-O; never launch."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time

HERE = Path(__file__).resolve().parent
REGIONS = {
    'fetch_and_dispatch': (0x124726, 0x124a98),
    'callmethod_candidate': (0x124c2b, 0x124cc2),
    'setmember_candidate': (0x125294, 0x1252ae),
    'pop_candidate': (0x125cab, 0x125cdc),
    'dispatch_table': (0x12cf44, 0x12d1b4),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def macho(data):
    if data[:8] != bytes.fromhex('cffaedfe07000001'):
        raise ValueError('expected little-endian x86_64 Mach-O')
    count, size = struct.unpack_from('<II', data, 16)
    end = 32 + size
    if end > len(data):
        raise ValueError('truncated load commands')
    offset, segments, uuid = 32, [], None
    for _ in range(count):
        command, length = struct.unpack_from('<II', data, offset)
        if length < 8 or offset + length > end:
            raise ValueError('invalid load command')
        if command == 0x19:
            name, address, vmsize, fileoff, filesize = struct.unpack_from('<16sQQQQ', data, offset + 8)
            segments.append(dict(name=name.rstrip(b'\0').decode(), vmaddr=address,
                                 vmsize=vmsize, fileoff=fileoff, filesize=filesize))
        elif command == 0x1b:
            uuid = data[offset + 8:offset + 24].hex()
        offset += length
    if offset != end or uuid is None:
        raise ValueError('incomplete load commands')
    return dict(uuid=uuid, segments=segments, header_hex=data[:end].hex())


def file_offset(module, address, length):
    matches = [s for s in module['segments']
               if s['vmaddr'] <= address and address + length <= s['vmaddr'] + s['filesize']]
    if len(matches) != 1:
        raise ValueError('address has no unique file-backed segment')
    segment = matches[0]
    return segment['fileoff'] + address - segment['vmaddr']


def main():
    started = time.monotonic()
    receipt = json.loads((HERE.parent / 's266/native-receipt.json').read_text())
    binary = receipt['engine']
    raw = Path(binary).read_bytes()
    digest = sha(raw)
    if digest != receipt['files'][binary]:
        raise ValueError('binary differs from receipt')
    module = macho(raw)
    base = next(s['vmaddr'] for s in module['segments'] if s['name'] == '__TEXT')
    regions, checks = {}, []
    for name, (start, end) in REGIONS.items():
        address = base + start
        offset = file_offset(module, address, end - start)
        data = raw[offset:offset + end - start]
        regions[name] = dict(module_relative=start, file_offset=offset, size=len(data),
                             hex=data.hex(), sha256=sha(data))
        if name == 'dispatch_table':
            continue
        command = ['objdump', '-d', '--x86-asm-syntax=intel',
                   '--start-address=' + hex(address), '--stop-address=' + hex(base + end), binary]
        tick = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=60)
        if result.returncode:
            raise ValueError(result.stderr.decode())
        log = name + '.txt'
        (HERE / log).write_bytes(result.stdout + result.stderr)
        checks.append(dict(command=command, exit_code=result.returncode, log=log,
                           sha256=sha(result.stdout + result.stderr), wall_seconds=time.monotonic() - tick))
    report = dict(binary=binary, binary_sha256=digest, binary_size=len(raw),
                  module=module, image_base=base, regions=regions, checks=checks,
                  player_launches=0, memory_reads=0, elapsed_seconds=time.monotonic() - started,
                  limitation='Static file extraction only. Unsigned slide-free addresses are not live PCs.')
    (HERE / 'native-audit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()

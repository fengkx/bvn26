"""Extract one static read wrapper from the receipt-matching player; never launch it."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import time

HERE = Path(__file__).resolve().parent
EXPECTED_SHA = '8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be'
START = 0x1004b3440
END = 0x1004b35f0
STUB = 0x100fb5baa


def sha(data):
    return hashlib.sha256(data).hexdigest()


def extract(binary):
    if sha(binary) != EXPECTED_SHA:
        raise ValueError('different player executable')
    if binary[:4] != bytes.fromhex('cffaedfe'):
        raise ValueError('expected little-endian Mach-O 64')
    offset = 32
    segments = []
    for _ in range(struct.unpack_from('<I', binary, 16)[0]):
        command, size = struct.unpack_from('<II', binary, offset)
        if command == 0x19:
            name = binary[offset + 8:offset + 24].rstrip(b'\0').decode()
            address, virtual_size, file_offset, file_size = struct.unpack_from('<QQQQ', binary, offset + 24)
            segments.append({'name': name, 'address': address, 'virtual_size': virtual_size,
                             'file_offset': file_offset, 'file_size': file_size})
        offset += size
    text = next(s for s in segments if s['name'] == '__TEXT')

    def region(address, size):
        relative = address - text['address']
        if not 0 <= relative <= text['file_size'] - size:
            raise ValueError('range outside file-backed text')
        file_offset = text['file_offset'] + relative
        data = binary[file_offset:file_offset + size]
        return {'address': address, 'file_offset': file_offset, 'size': size,
                'hex': data.hex(), 'sha256': sha(data)}

    return {'binary_sha256': sha(binary), 'binary_size': len(binary),
            'header_load_commands_hex': binary[:offset].hex(), 'text_segment': text,
            'wrapper': region(START, END - START), 'stub': region(STUB, 6),
            'kind': 'static_file_bytes_not_executed_or_consumed_bytes'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    result = extract(args.binary.read_bytes())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'extraction_seconds': time.monotonic() - start,
                      'binary_sha256': result['binary_sha256'], 'player_launches': 0}))


if __name__ == '__main__':
    main()

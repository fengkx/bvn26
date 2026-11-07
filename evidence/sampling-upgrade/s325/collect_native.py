"""Read a pinned Mach-O symbol table without launching or attaching to the player."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

PIN = '8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be'


def inventory(data):
    if hashlib.sha256(data).hexdigest() != PIN:
        raise ValueError('unexpected player binary')
    if data[:4] != b'\xcf\xfa\xed\xfe':
        raise ValueError('expected little-endian Mach-O 64')
    offset = 32
    tables = []
    for _ in range(struct.unpack_from('<I', data, 16)[0]):
        cmd, size = struct.unpack_from('<II', data, offset)
        if size < 8 or offset + size > len(data):
            raise ValueError('invalid load command')
        if cmd == 2:
            symbol_offset, count, string_offset, string_size = struct.unpack_from('<IIII', data, offset + 8)
            strings = data[string_offset:string_offset + string_size]
            entries = []
            for index in range(count):
                at = symbol_offset + index * 16
                name_at, kind, section, desc, value = struct.unpack_from('<IBBHQ', data, at)
                end = strings.index(b'\0', name_at)
                entries.append({'index': index, 'file_offset': at,
                                'entry_hex': data[at:at + 16].hex(),
                                'name': strings[name_at:end].decode('utf-8'),
                                'n_type': kind, 'n_sect': section,
                                'n_desc': desc, 'n_value': value})
            tables.append({'load_command_offset': offset, 'symbol_offset': symbol_offset,
                           'count': count, 'string_offset': string_offset,
                           'string_size': string_size, 'entries': entries})
        offset += size
    if len(tables) != 1:
        raise ValueError('expected one LC_SYMTAB')
    return {'binary_sha256': PIN, 'symbol_table': tables[0],
            'live_module_binding': None, 'object_layout': None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(inventory(args.binary.read_bytes()), indent=2) + '\n')

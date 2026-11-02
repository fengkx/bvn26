"""Pin allocator import bytes; import addresses do not identify AImain objects."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from audit_facility import BINARY, EXPECTED


def pin(binary, indirect):
    data = binary.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise ValueError('Player differs from s261 receipt')
    magic, _, _, _, ncmds, _, _, _ = struct.unpack_from('<8I', data)
    if magic != 0xfeedfacf:
        raise ValueError('Expected little-endian Mach-O 64')
    offset, sections, uuid = 32, [], None
    for _ in range(ncmds):
        cmd, size = struct.unpack_from('<II', data, offset)
        if cmd == 0x1b:
            uuid = data[offset + 8:offset + 24].hex()
        if cmd == 0x19:
            nsects = struct.unpack_from('<I', data, offset + 64)[0]
            for index in range(nsects):
                at = offset + 72 + index * 80
                name, segment, addr, length, file_offset = struct.unpack_from('<16s16sQQI', data, at)
                sections.append((segment.rstrip(b'\0').decode(), name.rstrip(b'\0').decode(), addr, length, file_offset))
        offset += size
    rows = []
    for address, name in re.findall(r'^(0x[0-9a-f]+)\s+\d+\s+_(malloc|calloc|realloc|free)$', indirect, re.M):
        address = int(address, 16)
        segment, section, start, length, file_start = next(s for s in sections if s[2] <= address < s[2] + s[3])
        width = 6 if section == '__stubs' else 8
        file_offset = file_start + address - start
        raw = data[file_offset:file_offset + width]
        row = {'symbol': name, 'segment': segment, 'section': section,
               'unslid_address': hex(address), 'file_offset': file_offset, 'bytes_hex': raw.hex()}
        if section == '__stubs':
            if raw[:2] != b'\xff\x25':
                raise ValueError('Expected x86_64 RIP-relative indirect jump')
            row['indirect_slot_unslid_address'] = hex(address + 6 + struct.unpack('<i', raw[2:])[0])
        rows.append(row)
    if len(rows) != 8:
        raise ValueError('Expected four stubs and four pointer slots')
    for row in rows:
        if row['section'] == '__stubs':
            if not any(other['symbol'] == row['symbol'] and other['unslid_address'] == row['indirect_slot_unslid_address'] for other in rows):
                raise ValueError('Stub/indirect symbol disagreement')
    return {'binary_sha256': EXPECTED, 'module_uuid_hex': uuid, 'imports': rows,
            'slot_resolver': None, 'saved_reference_resolver': None,
            'object_allocator_or_destructor': None,
            'limitation': 'On-disk import trampolines and initial pointer bytes only; no live address, object identity, allocation/free event or pool coverage.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    args.output.write_text(json.dumps(pin(BINARY, (here / 'facility/indirect-symbols.txt').read_text()), indent=2) + '\n')
